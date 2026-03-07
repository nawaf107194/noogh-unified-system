import pytest

from runpod_teacher.trajectory_recorder import TrajectoryRecorder

def test_create_tables_happy_path(mocker):
    # Create a mock connection object
    mock_conn = mocker.Mock()
    
    # Initialize the TrajectoryRecorder with the mock connection
    trajectory_recorder = TrajectoryRecorder(mock_conn)
    
    # Call the _create_tables method
    trajectory_recorder._create_tables()
    
    # Assert that the executescript method was called with the correct SQL script
    expected_sql_script = """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            total_tasks INTEGER DEFAULT 0,
            successful_tasks INTEGER DEFAULT 0,
            teacher_model TEXT,
            notes TEXT
        );
        
        CREATE TABLE IF NOT EXISTS trajectories (
            trajectory_id TEXT PRIMARY KEY,
            session_id TEXT REFERENCES sessions(session_id),
            task_category TEXT NOT NULL,
            task_prompt TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            
            -- Full conversation (messages format)
            messages_json TEXT NOT NULL,
            
            -- Teacher response
            teacher_response TEXT NOT NULL,
            
            -- Extracted tool calls
            tool_calls_json TEXT,
            
            -- Metadata
            input_tokens INTEGER,
            output_tokens INTEGER,
            latency_ms INTEGER,
            quality_score REAL,
            
            created_at TEXT NOT NULL,
            
            -- For training export
            exported INTEGER DEFAULT 0
        );
        
        CREATE INDEX IF NOT EXISTS idx_trajectories_category 
            ON trajectories(task_category);
        CREATE INDEX IF NOT EXISTS idx_trajectories_exported 
            ON trajectories(exported);
        CREATE INDEX IF NOT EXISTS idx_trajectories_quality 
            ON trajectories(quality_score DESC);
    """
    mock_conn.executescript.assert_called_once_with(expected_sql_script)
    
    # Assert that the commit method was called
    mock_conn.commit.assert_called_once()

def test_create_tables_empty_input(mocker):
    # Create a mock connection object
    mock_conn = mocker.Mock()
    
    # Initialize the TrajectoryRecorder with the mock connection
    trajectory_recorder = TrajectoryRecorder(mock_conn)
    
    # Call the _create_tables method with an empty input (though there's no input parameter, this test is more about ensuring it doesn't break with unexpected inputs)
    trajectory_recorder._create_tables()
    
    # Assert that the executescript method was called
    mock_conn.executescript.assert_called_once()
    
    # Assert that the commit method was called
    mock_conn.commit.assert_called_once()

def test_create_tables_none_input(mocker):
    # Create a mock connection object
    mock_conn = mocker.Mock()
    
    # Initialize the TrajectoryRecorder with the mock connection
    trajectory_recorder = TrajectoryRecorder(mock_conn)
    
    # Call the _create_tables method with None (though there's no input parameter, this test is more about ensuring it doesn't break with unexpected inputs)
    trajectory_recorder._create_tables(None)
    
    # Assert that the executescript method was called
    mock_conn.executescript.assert_called_once()
    
    # Assert that the commit method was called
    mock_conn.commit.assert_called_once()

def test_create_tables_boundary_cases(mocker):
    # Create a mock connection object
    mock_conn = mocker.Mock()
    
    # Initialize the TrajectoryRecorder with the mock connection
    trajectory_recorder = TrajectoryRecorder(mock_conn)
    
    # Call the _create_tables method with boundary cases (though there's no input parameter, this test is more about ensuring it doesn't break with unexpected inputs)
    trajectory_recorder._create_tables()
    
    # Assert that the executescript method was called
    mock_conn.executescript.assert_called_once()
    
    # Assert that the commit method was called
    mock_conn.commit.assert_called_once()

def test_create_tables_error_cases(mocker):
    # Create a mock connection object
    mock_conn = mocker.Mock()
    
    # Initialize the TrajectoryRecorder with the mock connection
    trajectory_recorder = TrajectoryRecorder(mock_conn)
    
    # Mock an error scenario where executescript raises an exception
    mock_conn.executescript.side_effect = Exception("Database error")
    
    # Call the _create_tables method and assert it doesn't raise exceptions (it should handle them gracefully)
    with pytest.raises(Exception) as exc_info:
        trajectory_recorder._create_tables()
    
    # Assert that the executescript method was called
    mock_conn.executescript.assert_called_once()
    
    # Assert that the commit method was not called
    mock_conn.commit.assert_not_called()