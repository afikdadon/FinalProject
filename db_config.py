"""
db_config.py
-----------
Description:
   Database configuration settings for the Geometric Learning System.
   Contains connection parameters for SQL Server instances.
   Configured for local development with multiple developer setups.

Author: Karin Hershko and Afik Dadon
Date: February 2024
"""

# Afik
DB_CONFIG = {
    'driver': 'SQL Server',
    'server': 'LAPTOP-7P25LDBF\SQLEXPRESS02',
    'database': 'FinalProject',
    'trusted_connection': 'yes'
}


# Karin
# DB_CONFIG = {
#    'driver': 'SQL Server',
#    'server': 'OG-PROLECTS\SQLEXPRESS',
#    'database': 'FinalProject',
#    'trusted_connection': 'yes'
# }
