# Geometry_Manager.py -  manages the weights of the triangles.
from typing import Dict, List, Tuple, Optional
import pyodbc
import math
from flask import session
from datetime import datetime, timedelta
from db_utils import get_db_connection


class Geometry_Manager:
    def __init__(self):
        self.conn = get_db_connection()
        self._initialize_session_state()

    def _initialize_session_state(self):
        if 'geometry_state' not in session:
            session['geometry_state'] = {
                'triangle_weights': {
                    0: 0.25,  # General triangle
                    1: 0.25,  # Equilateral
                    2: 0.25,  # Isosceles
                    3: 0.25  # Right
                },
                'theorem_weights': self._initialize_theorem_weights(),
                'asked_questions': [],  # List to store asked questions
                'asked_questions_texts': [],  # List to store question texts
                'questions_count': 0,  # Counter for questions
                'last_activity_time': datetime.now().isoformat(),
            }

    def _initialize_theorem_weights(self) -> Dict[int, float]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT theorem_id FROM Theorems WHERE active = 1")
        return {theorem[0]: 0.01 for theorem in cursor.fetchall()}

    def check_timeout(self) -> bool:
        print("Checking timeout...")
        state = session.get('geometry_state', {})

        if 'last_activity_time' not in state:
            print("No last_activity_time in session")
            return False

        last_activity = datetime.fromisoformat(state.get('last_activity_time'))
        current_time = datetime.now()
        time_diff = current_time - last_activity

        print(f"Last activity: {last_activity}")
        print(f"Current time: {current_time}")
        print(f"Time difference: {time_diff}")

        is_timeout = time_diff > timedelta(seconds=10)
        print(f"Is timeout? {is_timeout}")

        return is_timeout

    def update_activity_time(self):
        print("Updating activity time...")
        state = session['geometry_state']
        current_time = datetime.now()
        state['last_activity_time'] = current_time.isoformat()
        session.modified = True
        print(f"Updated last_activity_time to: {current_time}")

    def get_questions_history(self) -> dict:
        state = session['geometry_state']
        return {
            'asked_questions': state['asked_questions'],
            'asked_questions_texts': state['asked_questions_texts'],
            'questions_count': state['questions_count']
        }

    def get_next_question(self, is_admin: bool = False) -> Tuple[Optional[int], Optional[str], Optional[Dict]]:
        state = session['geometry_state']
        debug_info = self.get_debug_info() if is_admin else None

        try:
            self.update_activity_time()
            cursor = self.conn.cursor()
            cursor.execute("SELECT question_id, question_text FROM Questions WHERE active = 1")
            all_questions = cursor.fetchall()

            asked_questions = state['asked_questions']
            excluded_questions = set(asked_questions[-10:] if len(asked_questions) >= 10 else asked_questions)

            question_scores = {}
            for question in all_questions:
                question_id = question[0]
                if question_id not in excluded_questions:
                    # Check triangle relevance first
                    cursor.execute("""
                        SELECT DISTINCT ttm.triangle_id, ttm.connection_strength
                        FROM TheoremQuestionMatrix tqm
                        JOIN TheoremTriangleMatrix ttm ON tqm.theorem_id = ttm.theorem_id
                        WHERE tqm.question_id = ? AND tqm.relevance = 1
                    """, (question_id,))

                    # Calculate triangle relevance
                    triangle_relevance = 0
                    has_valid_triangle = False
                    for triangle_id, strength in cursor.fetchall():
                        triangle_weight = state['triangle_weights'].get(triangle_id, 0)
                        if triangle_weight > 0:
                            has_valid_triangle = True
                            triangle_relevance += strength * triangle_weight

                    # Only score questions that are relevant to triangles with non-zero weights
                    if has_valid_triangle:
                        info_gain = self._calculate_information_gain(question_id)
                        theorem_weight = self._get_theorem_weight_for_question(question_id)
                        # Modified scoring formula that prioritizes triangle relevance
                        question_scores[question_id] = info_gain * theorem_weight * (1 + triangle_relevance)

            if not question_scores:
                return None, None, debug_info

            best_question_id = max(question_scores.items(), key=lambda x: x[1])[0]
            cursor.execute("SELECT question_text FROM Questions WHERE question_id = ?", (best_question_id,))
            question_text = cursor.fetchone()[0]

            state['asked_questions'].append(best_question_id)
            state['asked_questions_texts'].append(question_text)
            state['questions_count'] = len(state['asked_questions'])
            session.modified = True

            return best_question_id, question_text, debug_info

        except Exception as e:
            print(f"Error in get_next_question: {str(e)}")
            return None, None, debug_info

    def process_answer(self, question_id: int, answer: str):
        state = session['geometry_state']

        # Update weights without resetting question history
        self._update_triangle_weights(question_id, answer)
        self._update_theorem_weights()
        self.update_activity_time()
        session.modified = True


    def get_debug_info(self) -> Dict:
        state = session.get('geometry_state', {})
        cursor = self.conn.cursor()

        # Get theorem texts
        cursor.execute("SELECT theorem_id, theorem_text FROM Theorems WHERE active = 1")
        theorem_texts = {row[0]: row[1] for row in cursor.fetchall()}

        # Get question texts
        cursor.execute("SELECT question_id, question_text FROM Questions WHERE active = 1")
        question_texts = {row[0]: row[1] for row in cursor.fetchall()}

        asked_questions = list(state.get('asked_questions', set()))
        print('asked_questions:', asked_questions)

        debug_info = {
            'triangle_weights': state.get('triangle_weights', {}),
            'theorem_weights': state.get('theorem_weights', {}),
            'theorem_texts': theorem_texts,
            'question_texts': question_texts,
            'asked_questions': list(state.get('asked_questions', set()))
        }

        # Add question scores
        available_questions = self._get_available_questions()
        question_scores = {}
        calculations = {
            'current_entropy': self._calculate_entropy(list(state['triangle_weights'].values())),
            'info_gain_details': [],
            'final_scores': []
        }

        for question in available_questions:
            question_id = question[0]
            info_gain = self._calculate_information_gain(question_id)
            theorem_weight = self._get_theorem_weight_for_question(question_id)
            score = info_gain * (1 + theorem_weight)
            question_scores[question_id] = score

            calculations['info_gain_details'].append(
                f"שאלה {question_id} - {question_texts.get(question_id, '')}:\n"
                f"Information Gain: {info_gain:.4f}\n"
                f"משקל משפטים קשורים: {theorem_weight:.4f}\n"
                f"ציון סופי = {info_gain:.4f} × (1 + {theorem_weight:.4f}) = {score:.4f}\n"
                "---"
            )

        sorted_scores = sorted(question_scores.items(), key=lambda x: x[1], reverse=True)
        calculations['final_scores'] = "\n".join(
            f"שאלה {q_id} - {question_texts.get(q_id, '')}: {score:.4f}"
            for q_id, score in sorted_scores
        )

        debug_info['question_scores'] = question_scores
        debug_info['calculations'] = calculations

        return debug_info

    def get_relevant_theorems(self, base_threshold: float = 0.01) -> List[Tuple[int, str, float]]:
        state = session['geometry_state']
        num_questions = len(state['asked_questions'])

        cursor = self.conn.cursor()
        theorems = []

        if num_questions == 1:
            cursor.execute("SELECT theorem_id, theorem_text FROM Theorems WHERE active = 1")
            all_theorems = cursor.fetchall()
            cursor.close()

            if not all_theorems:
                print("WARNING: No active theorems found in database!")
                return []

            weight = 0.01
            theorems = [(theorem_id, theorem_text, weight) for theorem_id, theorem_text in all_theorems]
            return theorems

        increment_factor = 0.05
        threshold = base_threshold + (num_questions * increment_factor)

        # Use a new cursor for each theorem query
        for theorem_id, weight in state['theorem_weights'].items():
            if weight >= threshold:
                with self.conn.cursor() as theorem_cursor:
                    theorem_cursor.execute("SELECT theorem_text FROM Theorems WHERE theorem_id = ?", (theorem_id,))
                    theorem_text = theorem_cursor.fetchone()[0]
                    theorems.append((theorem_id, theorem_text, weight))

        return sorted(theorems, key=lambda x: x[2], reverse=True)

    def _get_available_questions(self) -> List[Tuple[int, str]]:
        state = session['geometry_state']
        cursor = self.conn.cursor()

        # Get all asked questions
        asked_questions = list(state['asked_questions'])

        print(f"\nDebug - All asked questions so far: {asked_questions}")  # Debug log

        # If we haven't asked at least 10 different questions yet,
        # exclude ALL previously asked questions
        if len(asked_questions) < 10:
            if asked_questions:
                placeholders = ','.join(['?' for _ in asked_questions])
                query = f"""
                    SELECT question_id, question_text 
                    FROM Questions 
                    WHERE active = 1 
                    AND question_id NOT IN ({placeholders})
                """
                cursor.execute(query, asked_questions)
            else:
                cursor.execute("""
                    SELECT question_id, question_text 
                    FROM Questions 
                    WHERE active = 1
                """)
        else:
            # We have asked at least 10 questions
            # Get the last 10 questions to exclude
            recent_five = asked_questions[-10:]
            placeholders = ','.join(['?' for _ in recent_five])
            query = f"""
                SELECT question_id, question_text 
                FROM Questions 
                WHERE active = 1 
                AND question_id NOT IN ({placeholders})
            """
            cursor.execute(query, recent_five)

        available = cursor.fetchall()
        print(f"\nDebug - Available questions after exclusion: {[q[0] for q in available]}")  # Debug log

        cursor.close()
        return available

    def _calculate_information_gain(self, question_id: int) -> float:
        state = session['geometry_state']
        current_entropy = self._calculate_entropy(list(state['triangle_weights'].values()))

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT answer_type 
            FROM AnswerMultipliers 
            WHERE question_id = ?
        """, (question_id,))
        possible_answers = cursor.fetchall()

        expected_entropy = 0
        for answer in possible_answers:
            answer_type = answer[0]
            new_weights = self._simulate_answer_weights(question_id, answer_type)
            entropy = self._calculate_entropy(list(new_weights.values()))
            p_answer = 1.0 / len(possible_answers)
            expected_entropy += p_answer * entropy

        ig = current_entropy - expected_entropy
        return ig

    def _calculate_entropy(self, probabilities: List[float]) -> float:
        # Filter out zero probabilities before calculating entropy
        non_zero_probs = [p for p in probabilities if p > 0]
        if not non_zero_probs:
            return 0
        return -sum(p * math.log2(p) if p > 0 else 0 for p in non_zero_probs)

    def _update_triangle_weights(self, question_id: int, answer: str):
        state = session['geometry_state']
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT triangle_id, multiplier 
            FROM AnswerMultipliers 
            WHERE question_id = ? AND answer_type = ?
        """, (question_id, answer))

        multipliers = cursor.fetchall()
        cursor.close()

        if not multipliers:
            return

        total = 0
        for triangle_id, multiplier in multipliers:
            state['triangle_weights'][triangle_id] *= multiplier
            total += state['triangle_weights'][triangle_id]

        # Normalize weights
        if total > 0:
            for triangle_id in state['triangle_weights']:
                state['triangle_weights'][triangle_id] /= total

        session.modified = True

    def _update_theorem_weights(self):
        state = session['geometry_state']
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT theorem_id, triangle_id, connection_strength 
            FROM TheoremTriangleMatrix
        """)

        new_weights = {}
        for theorem_id, triangle_id, strength in cursor.fetchall():
            if theorem_id not in new_weights:
                new_weights[theorem_id] = 0
            new_weights[theorem_id] += state['triangle_weights'][triangle_id] * strength

        state['theorem_weights'] = new_weights
        session.modified = True

    def _get_theorem_weight_for_question(self, question_id: int) -> float:
        state = session['geometry_state']
        cursor = self.conn.cursor()

        # First get theorems related to this question
        cursor.execute("""
            SELECT theorem_id 
            FROM TheoremQuestionMatrix 
            WHERE question_id = ? AND relevance = 1
        """, (question_id,))

        related_theorems = cursor.fetchall()

        # Get the triangle weights for each theorem
        weight_sum = 0
        for theorem in related_theorems:
            theorem_id = theorem[0]
            cursor.execute("""
                SELECT triangle_id, connection_strength 
                FROM TheoremTriangleMatrix 
                WHERE theorem_id = ?
            """, (theorem_id,))

            # For each theorem, consider only triangles with non-zero weights
            for triangle_id, strength in cursor.fetchall():
                triangle_weight = state['triangle_weights'].get(triangle_id, 0)
                if triangle_weight > 0:
                    weight_sum += strength * triangle_weight

        return min(weight_sum, 1.0)

    def _simulate_answer_weights(self, question_id: int, answer: str) -> Dict[int, float]:
        state = session['geometry_state']
        new_weights = state['triangle_weights'].copy()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT triangle_id, multiplier 
            FROM AnswerMultipliers 
            WHERE question_id = ? AND answer_type = ?
        """, (question_id, answer))

        total = 0
        for triangle_id, multiplier in cursor.fetchall():
            new_weights[triangle_id] *= multiplier
            total += new_weights[triangle_id]

        if total > 0:
            for triangle_id in new_weights:
                new_weights[triangle_id] /= total

        return new_weights

    def reset_session(self):
        session['geometry_state'] = {
            'triangle_weights': {
                0: 0.25,
                1: 0.25,
                2: 0.25,
                3: 0.25
            },
            'theorem_weights': self._initialize_theorem_weights(),
            'asked_questions': [],
            'asked_questions_texts': [],
            'questions_count': 0,
            'last_activity_time': datetime.now().isoformat()
        }
        session.modified = True

        def _get_question_triangle_relevance(self, question_id: int) -> float:
            state = session['geometry_state']
            cursor = self.conn.cursor()

            # Get all theorems related to this question
            cursor.execute("""
                SELECT DISTINCT t.theorem_id, t.category, ttm.triangle_id, ttm.connection_strength
                FROM TheoremQuestionMatrix tqm
                JOIN Theorems t ON tqm.theorem_id = t.theorem_id
                JOIN TheoremTriangleMatrix ttm ON t.theorem_id = ttm.theorem_id
                WHERE tqm.question_id = ? AND tqm.relevance = 1
            """, (question_id,))

            relevance_scores = {0: 0, 1: 0, 2: 0, 3: 0}  # Initialize scores for each triangle type

            for _, _, triangle_id, strength in cursor.fetchall():
                relevance_scores[triangle_id] += strength

            # Calculate weighted relevance based on current triangle probabilities
            total_relevance = 0
            for triangle_id, score in relevance_scores.items():
                triangle_weight = state['triangle_weights'].get(triangle_id, 0)
                total_relevance += score * triangle_weight

            return total_relevance