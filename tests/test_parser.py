import pytest
import os
import sqlite3
from src.parser import AcmiParser
from src.db_init import init_db

def test_acmi_parser_integrity():
    # Setup: Create a temporary test DB
    test_db = "data/test_flight.db"
    if os.path.exists(test_db): os.remove(test_db)
    
    # Initialize DB
    init_db(test_db)
    # Note: Using the real init_db script is now correctly implemented
    
    conn = sqlite3.connect(test_db)
    # For simplicity in this test, we run the parser which creates its own
    parser = AcmiParser(db_path=test_db)
    
    # Mock ACMI content
    test_acmi = "data/samples/test_integrity.acmi"
    os.makedirs(os.path.dirname(test_acmi), exist_ok=True)
    with open(test_acmi, "w") as f:
        f.write("0,MissionTitle=Test_Unit\n#0.00\n1,T=10|20|30|0|0|0,Name=Test_Jet\n")
    
    # Run Parser
    parser.parse_file(test_acmi)
    
    # Verify Data
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    sortie = cursor.execute("SELECT mission_name, aircraft_type FROM sorties").fetchone()
    assert sortie[0] == "Test_Unit"
    assert sortie[1] == "Test_Jet"
    
    telemetry_count = cursor.execute("SELECT count(*) FROM telemetry").fetchone()[0]
    assert telemetry_count == 1
    
    # Cleanup
    conn.close()
    if os.path.exists(test_db): os.remove(test_db)
    if os.path.exists(test_acmi): os.remove(test_acmi)

if __name__ == "__main__":
    pytest.main([__file__])
