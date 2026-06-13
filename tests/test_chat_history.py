import pytest
import tempfile
import os
from app.core.chat_history import ChatHistoryManager

def test_chat_history_manager():
    # Use a temporary file for testing DB
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    try:
        manager = ChatHistoryManager(db_path=temp_db_path)
        
        # Test session creation
        session_id = "test-session-123"
        manager.create_session(session_id, "Test Chat Title")
        
        sessions = manager.get_sessions()
        assert len(sessions) == 1
        assert sessions[0]["id"] == session_id
        assert sessions[0]["title"] == "Test Chat Title"
        
        # Test adding messages
        manager.add_message(session_id, "user", "Hello assistant!")
        manager.add_message(
            session_id, 
            "assistant", 
            "Hello human!", 
            [{"content": "Doc 1 text", "metadata": {"source_file": "doc1.txt"}, "score": 0.99}]
        )
        
        messages = manager.get_messages(session_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello assistant!"
        
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hello human!"
        assert len(messages[1]["sources"]) == 1
        assert messages[1]["sources"][0]["content"] == "Doc 1 text"
        assert messages[1]["sources"][0]["metadata"]["source_file"] == "doc1.txt"
        
        # Test rename
        manager.rename_session(session_id, "Renamed Chat")
        sessions = manager.get_sessions()
        assert sessions[0]["title"] == "Renamed Chat"
        
        # Test delete
        manager.delete_session(session_id)
        sessions = manager.get_sessions()
        assert len(sessions) == 0
        messages = manager.get_messages(session_id)
        assert len(messages) == 0
        
    finally:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
