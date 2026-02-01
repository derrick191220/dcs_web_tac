import math

def generate_acmi(filename='data/samples/full_flight_sim.acmi'):
    header = """0,ReferenceTime=2026-02-01T10:00:00Z
0,RecordingPlayerName=Derrick_Pilot
0,MissionTitle=Full_Cycle_Test
"""
    with open(filename, 'w') as f:
        f.write(header)
        
        # Initial Position: Batumi Airport (approx)
        lat, lon = 41.61, 41.60
        alt = 0
        speed = 0 # knots
        
        # 1. Taxi (60 seconds)
        for t in range(0, 60):
            f.write(f"#{t:.2f}\n")
            f.write(f"1,T={lon}|{lat}|{alt}|0|0|130,Name=F-16C,Type=Aircraft+FixedWing,IAS={speed},G=1.0\n")
            lon += 0.00001
            speed = min(speed + 0.5, 20)

        # 2. Takeoff Run (30 seconds)
        for t in range(60, 90):
            f.write(f"#{t:.2f}\n")
            f.write(f"1,T={lon}|{lat}|{alt}|0|5|130,IAS={speed},G=1.1\n")
            lon += 0.0001 * (speed/20)
            speed += 5

        # 3. Climb (120 seconds)
        for t in range(90, 210):
            f.write(f"#{t:.2f}\n")
            f.write(f"1,T={lon}|{lat}|{alt}|10|15|130,IAS={speed},G=1.2\n")
            lon += 0.0005
            alt += 15
            speed = min(speed + 2, 450)

        # 4. Cruise & Maneuver (300 seconds)
        for t in range(210, 510):
            f.write(f"#{t:.2f}\n")
            roll = 30 * math.sin(t/10)
            f.write(f"1,T={lon}|{lat}|{alt}|{roll}|0|130,IAS={speed},G={1.0 + abs(roll/10)}\n")
            lon += 0.001
            lat += 0.0002 * math.cos(t/20)

        # 5. Descent & Landing (180 seconds)
        for t in range(510, 690):
            f.write(f"#{t:.2f}\n")
            f.write(f"1,T={lon}|{lat}|{alt}|0|-5|130,IAS={speed},G=1.0\n")
            lon += 0.0003
            alt = max(0, alt - 10)
            speed = max(150, speed - 2)
            if alt == 0:
                speed = max(0, speed - 10)

        f.write(f"#690.00\n")
        f.write(f"1,T={lon}|{lat}|0|0|0|130,IAS=0,G=1.0\n")

    print(f"Generated high-fidelity sample: {filename}")

if __name__ == "__main__":
    generate_acmi()
