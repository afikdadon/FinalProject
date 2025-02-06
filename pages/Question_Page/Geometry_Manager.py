"""
Geometry_Manager.py
------------------
Description:
    A core component of the Geometric Learning System that manages the intelligent selection
    of questions and theorems in a geometry-based educational system. This manager uses
    weighted probabilities and information gain to guide students through geometry problems,
    focusing specifically on triangle-related theorems and properties.

Main Components:
    - Triangle Weight Management: Handles probability distributions for different triangle types
    - Question Selection: Uses information gain to choose optimal questions
    - Theorem Management: Tracks and updates relevance of geometric theorems
    - Session Management: Maintains user session state and progress

Triangle Types:
    0: General triangle
    1: Equilateral triangle
    2: Isosceles triangle
    3: Right triangle

Author: Karin Hershko and Afik Dadon
Date: February 2024
"""
from typing import Dict, List, Tuple, Optional
import math
import random
from flask import session
from datetime import datetime, timedelta
from db_utils import get_db_connection


class Geometry_Manager:
    def __init__(self):
        """Initialize database connection and session state."""
        self.conn = get_db_connection()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Set up initial session state with default weights if not already present."""
        if 'geometry_state' not in session:
            session['geometry_state'] = {
                'triangle_weights': {
                    0: 0.25,  # General triangle
                    1: 0.25,  # Equilateral
                    2: 0.25,  # Isosceles
                    3: 0.25  # Right
                },
                'theorem_weights': self._initialize_theorem_weights(),
                'asked_questions': [],  # Track question IDs
                'asked_questions_texts': [],  # Track question texts
                'questions_count': 0,  # Total questions asked
                'last_activity_time': datetime.now().isoformat(),
            }

    def _initialize_theorem_weights(self) -> Dict[int, float]:
        """Initialize all active theorems with minimal base weight."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT theorem_id FROM Theorems WHERE active = 1")
        return {theorem[0]: 0.01 for theorem in cursor.fetchall()}

    def check_timeout(self) -> bool:
        """Check if session has timed out (15 minutes threshold)."""
        state = session.get('geometry_state', {})
        if 'last_activity_time' not in state:
            return False

        last_activity = datetime.fromisoformat(state.get('last_activity_time'))
        current_time = datetime.now()
        return (current_time - last_activity) > timedelta(minutes=15)

    def update_activity_time(self):
        """Update the last activity timestamp in session."""
        state = session['geometry_state']
        state['last_activity_time'] = datetime.now().isoformat()
        session.modified = True

    def get_questions_history(self) -> dict:
        """Return the history of asked questions and their count."""
        state = session['geometry_state']
        return {
            'asked_questions': state['asked_questions'],
            'asked_questions_texts': state['asked_questions_texts'],
            'questions_count': state['questions_count']
        }


    # === Question Selection and Processing ===
    def _get_easy_questions(self):
        """Retrieve all active questions marked as 'easy' (difficulty level 1)."""
        cursor = self.conn.cursor()
        cursor.execute("""
                   SELECT question_id, question_text 
                   FROM Questions 
                   WHERE difficulty_level = 1 AND active = 1
               """)
        return cursor.fetchall()

    def get_next_question(self, is_admin: bool = False) -> Tuple[Optional[int], Optional[str], Optional[Dict]]:
        """Select the most appropriate next question based on current weights and history."""
        state = session['geometry_state']
        debug_info = self.get_debug_info() if is_admin else None

        try:
            self.update_activity_time()

            # Handle first question - select random easy question
            if len(state['asked_questions']) == 0:
                easy_questions = self._get_easy_questions()
                if not easy_questions:
                    return None, None, debug_info

                selected_question = random.choice(easy_questions)
                question_id, question_text = selected_question[0], selected_question[1]

                # Update session state
                state['asked_questions'].append(question_id)
                state['asked_questions_texts'].append(question_text)
                state['questions_count'] = len(state['asked_questions'])
                session.modified = True

                return question_id, question_text, debug_info

            # Select subsequent questions based on weights and relevance
            cursor = self.conn.cursor()
            cursor.execute("SELECT question_id, question_text FROM Questions WHERE active = 1")
            all_questions = cursor.fetchall()

            # Avoid recently asked questions (last 10)
            asked_questions = state['asked_questions']
            excluded_questions = set(asked_questions[-10:] if len(asked_questions) >= 10 else asked_questions)

            # Score each potential question
            question_scores = {}
            for question in all_questions:
                question_id = question[0]
                if question_id not in excluded_questions:
                    # Check triangle relevance
                    cursor.execute("""
                           SELECT DISTINCT ttm.triangle_id, ttm.connection_strength
                           FROM TheoremQuestionMatrix tqm
                           JOIN TheoremTriangleMatrix ttm ON tqm.theorem_id = ttm.theorem_id
                           WHERE tqm.question_id = ? AND tqm.relevance = 1
                       """, (question_id,))

                    triangle_relevance = 0
                    has_valid_triangle = False
                    for triangle_id, strength in cursor.fetchall():
                        triangle_weight = state['triangle_weights'].get(triangle_id, 0)
                        if triangle_weight > 0:
                            has_valid_triangle = True
                            triangle_relevance += strength * triangle_weight

                    if has_valid_triangle:
                        info_gain = self._calculate_information_gain(question_id)
                        theorem_weight = self._get_theorem_weight_for_question(question_id)
                        question_scores[question_id] = info_gain * theorem_weight * (1 + triangle_relevance)

            if not question_scores:
                return None, None, debug_info

            # Select question with highest score
            best_question_id = max(question_scores.items(), key=lambda x: x[1])[0]
            cursor.execute("SELECT question_text FROM Questions WHERE question_id = ?", (best_question_id,))
            question_text = cursor.fetchone()[0]

            # Update session state
            state['asked_questions'].append(best_question_id)
            state['asked_questions_texts'].append(question_text)
            state['questions_count'] = len(state['asked_questions'])
            session.modified = True

            return best_question_id, question_text, debug_info

        except Exception as e:
            return None, None, debug_info

    def process_answer(self, question_id: int, answer: str):
        """Process user's answer and update weights accordingly."""
        state = session['geometry_state']
        self._update_triangle_weights(question_id, answer)
        self._update_theorem_weights()
        self.update_activity_time()
        session.modified = True


    # === Theorem Management ===
    def get_relevant_theorems(self, base_threshold: float = 0.01) -> List[Tuple[int, str, float, int]]:
        """Get list of relevant theorems based on current weights and question count."""
        state = session['geometry_state']
        num_questions = len(state['asked_questions'])

        cursor = self.conn.cursor()
        theorems = []

        # Special case for first question - return all theorems with base weight
        if num_questions == 1:
            cursor.execute("SELECT theorem_id, theorem_text, category FROM Theorems WHERE active = 1")
            all_theorems = cursor.fetchall()
            cursor.close()

            if not all_theorems:
                return []

            weight = 0.01
            theorems = [(theorem_id, theorem_text, weight, category)
                        for theorem_id, theorem_text, category in all_theorems]
            return theorems

        # Adjust threshold based on number of questions asked
        increment_factor = 0.05
        threshold = base_threshold + (num_questions * increment_factor)

        # Select theorems above threshold
        for theorem_id, weight in state['theorem_weights'].items():
            if weight >= threshold:
                with self.conn.cursor() as theorem_cursor:
                    theorem_cursor.execute(
                        "SELECT theorem_text, category FROM Theorems WHERE theorem_id = ?",
                        (theorem_id,)
                    )
                    theorem_data = theorem_cursor.fetchone()
                    theorem_text = theorem_data[0]
                    category = theorem_data[1]
                    theorems.append((theorem_id, theorem_text, weight, category))

        return sorted(theorems, key=lambda x: x[2], reverse=True)

    # === Weight Calculations and Updates ===
    def _calculate_information_gain(self, question_id: int) -> float:
        """Calculate information gain for a potential question."""
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

        return current_entropy - expected_entropy

    def _calculate_entropy(self, probabilities: List[float]) -> float:
        """Calculate Shannon entropy for given probability distribution."""
        non_zero_probs = [p for p in probabilities if p > 0]
        if not non_zero_probs:
            return 0
        return -sum(p * math.log2(p) if p > 0 else 0 for p in non_zero_probs)

    def _update_triangle_weights(self, question_id: int, answer: str):
        """Update triangle weights based on user's answer to a question.
        Applies multipliers from the database and normalizes resulting weights."""
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
        """Update theorem weights based on current triangle weights.
        Uses connection strengths from TheoremTriangleMatrix to calculate
        new weights for each theorem based on triangle probabilities."""
        state = session['geometry_state']
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT theorem_id, triangle_id, connection_strength 
            FROM TheoremTriangleMatrix
        """)

        new_weights = {}
        theorem_connections = {}

        # Group connections by theorem
        for theorem_id, triangle_id, strength in cursor.fetchall():
            if theorem_id not in theorem_connections:
                theorem_connections[theorem_id] = []
            if strength >= 0.9:  # Only consider strong connections
                theorem_connections[theorem_id].append((triangle_id, strength))

        # Calculate new weights
        for theorem_id, connections in theorem_connections.items():
            if not connections:
                new_weights[theorem_id] = 0
                continue

            # Multiply weights for required properties
            weight = 1.0
            for triangle_id, strength in connections:
                weight *= state['triangle_weights'][triangle_id]

            new_weights[theorem_id] = weight

        state['theorem_weights'] = new_weights
        session.modified = True

    def _get_theorem_weight_for_question(self, question_id: int) -> float:
        """Calculate the relevance weight of theorems for a specific question."""
        state = session['geometry_state']
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT theorem_id 
            FROM TheoremQuestionMatrix 
            WHERE question_id = ? AND relevance = 1
        """, (question_id,))

        related_theorems = cursor.fetchall()
        weight_sum = 0

        for theorem in related_theorems:
            theorem_id = theorem[0]
            cursor.execute("""
                SELECT triangle_id, connection_strength 
                FROM TheoremTriangleMatrix 
                WHERE theorem_id = ?
            """, (theorem_id,))

            for triangle_id, strength in cursor.fetchall():
                triangle_weight = state['triangle_weights'].get(triangle_id, 0)
                if triangle_weight > 0:
                    weight_sum += strength * triangle_weight

        return min(weight_sum, 1.0)

    def _simulate_answer_weights(self, question_id: int, answer: str) -> Dict[int, float]:
        """Simulate how weights would change for a given answer.
        Used in information gain calculations."""
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

    # === Session Management ===

    def reset_session(self):
        """Reset all session state to initial values."""
        session['geometry_state'] = {
            'triangle_weights': {
                0: 0.25,  # General triangle
                1: 0.25,  # Equilateral
                2: 0.25,  # Isosceles
                3: 0.25  # Right
            },
            'theorem_weights': self._initialize_theorem_weights(),
            'asked_questions': [],
            'asked_questions_texts': [],
            'questions_count': 0,
            'last_activity_time': datetime.now().isoformat()
        }
        session.modified = True

    # === Debug Information ===

    def get_debug_info(self) -> Dict:
        """Collect debug information about current system state.
        Used by administrators to monitor the system's decision-making process."""
        state = session.get('geometry_state', {})
        cursor = self.conn.cursor()

        # Get theorem and question information
        cursor.execute("SELECT theorem_id, theorem_text FROM Theorems WHERE active = 1")
        theorem_texts = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT question_id, question_text FROM Questions WHERE active = 1")
        question_texts = {row[0]: row[1] for row in cursor.fetchall()}

        # Prepare debug information
        debug_info = {
            'triangle_weights': state.get('triangle_weights', {}),
            'theorem_weights': state.get('theorem_weights', {}),
            'theorem_texts': theorem_texts,
            'question_texts': question_texts,
            'asked_questions': list(state.get('asked_questions', set()))
        }

        # Add calculation details
        available_questions = self._get_available_questions()
        question_scores = {}
        calculations = {
            'current_entropy': self._calculate_entropy(list(state['triangle_weights'].values())),
            'info_gain_details': [],
            'final_scores': []
        }

        # Calculate scores for available questions
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

        # Sort and format final scores
        sorted_scores = sorted(question_scores.items(), key=lambda x: x[1], reverse=True)
        calculations['final_scores'] = "\n".join(
            f"שאלה {q_id} - {question_texts.get(q_id, '')}: {score:.4f}"
            for q_id, score in sorted_scores
        )

        debug_info['question_scores'] = question_scores
        debug_info['calculations'] = calculations

        return debug_info

    def _get_available_questions(self) -> List[Tuple[int, str]]:
        """Get list of available questions that haven't been recently asked."""
        state = session['geometry_state']
        cursor = self.conn.cursor()
        asked_questions = list(state['asked_questions'])

        # Handle cases based on number of previously asked questions
        if len(asked_questions) < 10:
            if asked_questions:
                # Exclude all previously asked questions
                placeholders = ','.join(['?' for _ in asked_questions])
                query = f"""
                    SELECT question_id, question_text 
                    FROM Questions 
                    WHERE active = 1 
                    AND question_id NOT IN ({placeholders})
                """
                cursor.execute(query, asked_questions)
            else:
                # No questions asked yet - return all active questions
                cursor.execute("""
                    SELECT question_id, question_text 
                    FROM Questions 
                    WHERE active = 1
                """)
        else:
            # Exclude the 10 most recent questions
            recent_questions = asked_questions[-10:]
            placeholders = ','.join(['?' for _ in recent_questions])
            query = f"""
                SELECT question_id, question_text 
                FROM Questions 
                WHERE active = 1 
                AND question_id NOT IN ({placeholders})
            """
            cursor.execute(query, recent_questions)

        available = cursor.fetchall()
        cursor.close()
        return available