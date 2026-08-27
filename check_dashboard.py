"""Check if the dashboard is running and show current data."""
import urllib.request
import json

try:
    with urllib.request.urlopen("http://127.0.0.1:5000/api/overview", timeout=5) as resp:
        data = json.loads(resp.read())
        print("=" * 50)
        print("DASHBOARD IS RUNNING!")
        print("=" * 50)
        print(f"Tracker Status: {'RUNNING' if data['status']['running'] else 'STOPPED'}")
        print(f"Total Reports: {data['activity']['total_reports']}")
        print(f"Total Screenshots: {data['activity']['total_screenshots']}")
        print(f"Today's Reports: {data['activity']['today_reports']}")
        print(f"Data Size: {data['disk']['size_mb']} MB")
        print(f"Total Files: {data['disk']['file_count']}")
        print()
        print("Recent Reports:")
        for r in data.get("recent_reports", [])[:5]:
            print(f"  - {r['date']} {r['time']} ({r['size']/1024:.1f} KB)")
        print()
        print("Recent Screenshots:")
        for s in data.get("recent_screenshots", [])[:5]:
            print(f"  - {s['date']} {s['time']}")
        print()
        print("Daily Report Counts (last 7 days):")
        for d in data.get("daily_reports", []):
            print(f"  - {d['date']}: {d['count']} reports")
except Exception as e:
    print(f"Dashboard not reachable: {e}")