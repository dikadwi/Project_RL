from utils.rl_utils import generate_all_states
from db import mysql

ACTION_CODES = [101, 105, 102, 103, 106]


def init_q_table():
    """Inisialisasi tabel q_table dengan semua kombinasi state dan action."""
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS q_table (
            state VARCHAR(255) NOT NULL,
            action_code INT NOT NULL,
            q_value FLOAT DEFAULT 0,
            PRIMARY KEY (state, action_code)
        )
        """
    )
    for state in generate_all_states():
        for code in ACTION_CODES:
            cursor.execute(
                """
                INSERT INTO q_table (state, action_code, q_value)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE q_value = q_value
                """,
                (state, code, 0.0),
            )
    mysql.connection.commit()
    cursor.close()


if __name__ == "__main__":
    init_q_table()
