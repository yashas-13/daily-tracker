"""Daily Tracker - Native Windows Desktop Application."""
import os
import sys
import json
import time
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from PIL import Image, ImageTk

from tracker import config
from tracker.logger import log

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Colors
COLORS = {
    "bg": "#0f1117",
    "card": "#1a1d27",
    "hover": "#232733",
    "border": "#2a2e3a",
    "text": "#e4e6eb",
    "dim": "#8b8f9c",
    "accent": "#4f8cff",
    "accent_hover": "#3a6fd8",
    "green": "#4caf50",
    "red": "#f44336",
    "yellow": "#ffc107",
}


class TrackerApp(ctk.CTk):
    """Main desktop application window."""

    def __init__(self):
        super().__init__()
        
        self.title("Daily Tracker - Desktop App")
        self.geometry("1200x750")
        self.minsize(900, 600)
        
        # Tracker instance
        self.tracker = None
        self.tracker_thread = None
        
        # Data
        self.reports = []
        self.screenshots = []
        self.raw_files = []
        self.logs = []
        self.processes = []
        self.network = []
        
        # Current view
        self.current_view = "dashboard"
        self.current_report = None
        self.current_screenshot = None
        
        # Setup UI
        self._setup_ui()
        
        # Start background refresh
        self._start_refresh()
        
        # Load initial data
        self.after(500, self.refresh_all)
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self._setup_sidebar()
        
        # Main content area
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Show dashboard by default
        self._show_dashboard()
    
    def _setup_sidebar(self):
        """Set up the sidebar navigation."""
        self.sidebar = ctk.CTkFrame(self, width=200, fg_color=COLORS["card"], corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Header
        header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(20, 15))
        
        title = ctk.CTkLabel(header, text="📊 Daily Tracker", 
                            font=ctk.CTkFont(size=18, weight="bold"),
                            text_color=COLORS["accent"])
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(header, text="Desktop Control Panel",
                               font=ctk.CTkFont(size=11),
                               text_color=COLORS["dim"])
        subtitle.pack(anchor="w", pady=(2, 0))
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(header, fg_color="transparent")
        self.status_frame.pack(fill="x", pady=(15, 0))
        
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", 
                                       font=ctk.CTkFont(size=14),
                                       text_color=COLORS["red"])
        self.status_dot.pack(side="left", padx=(0, 5))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Stopped",
                                        font=ctk.CTkFont(size=12),
                                        text_color=COLORS["dim"])
        self.status_label.pack(side="left")
        
        # Navigation buttons
        nav_items = [
            ("dashboard", "📈", "Dashboard"),
            ("reports", "📄", "Reports"),
            ("screenshots", "📸", "Screenshots"),
            ("raw", "📁", "Raw Data"),
            ("processes", "⚙️", "Processes"),
            ("network", "🌐", "Network"),
            ("logs", "📋", "Logs"),
            ("settings", "⚡", "Settings"),
        ]
        
        self.nav_buttons = {}
        for key, icon, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}  {label}",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=COLORS["hover"],
                text_color=COLORS["dim"],
                anchor="w",
                height=40,
                corner_radius=8,
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn
        
        # Version
        version = ctk.CTkLabel(self.sidebar, text="v1.0.0",
                              font=ctk.CTkFont(size=10),
                              text_color=COLORS["dim"])
        version.pack(side="bottom", pady=10)
    
    def _navigate(self, view):
        """Navigate to a view."""
        self.current_view = view
        
        # Update nav button colors
        for key, btn in self.nav_buttons.items():
            if key == view:
                btn.configure(text_color=COLORS["accent"], fg_color=COLORS["hover"])
            else:
                btn.configure(text_color=COLORS["dim"], fg_color="transparent")
        
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Show the selected view
        if view == "dashboard":
            self._show_dashboard()
        elif view == "reports":
            self._show_reports()
        elif view == "screenshots":
            self._show_screenshots()
        elif view == "raw":
            self._show_raw()
        elif view == "processes":
            self._show_processes()
        elif view == "network":
            self._show_network()
        elif view == "logs":
            self._show_logs()
        elif view == "settings":
            self._show_settings()
    
    # ============ Dashboard View ============
    def _show_dashboard(self):
        """Show the dashboard view."""
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(header, text="Dashboard",
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(header, text="🔄 Refresh", width=100,
                                   command=self.refresh_all)
        refresh_btn.pack(side="right")
        
        # Stats cards
        stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        self.stat_cards = {}
        stats = [
            ("reports", "📄", "Total Reports"),
            ("screenshots", "📸", "Screenshots"),
            ("today", "📅", "Today's Reports"),
            ("size", "💾", "Data Size"),
        ]
        
        for i, (key, icon, label) in enumerate(stats):
            card = ctk.CTkFrame(stats_frame, fg_color=COLORS["card"], corner_radius=10,
                               border_width=1, border_color=COLORS["border"])
            card.grid(row=0, column=i, padx=5, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
            
            icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=24))
            icon_label.pack(pady=(15, 5))
            
            value_label = ctk.CTkLabel(card, text="0", 
                                      font=ctk.CTkFont(size=28, weight="bold"))
            value_label.pack()
            
            name_label = ctk.CTkLabel(card, text=label,
                                     font=ctk.CTkFont(size=11),
                                     text_color=COLORS["dim"])
            name_label.pack(pady=(5, 15))
            
            self.stat_cards[key] = value_label
        
        # Recent activity
        activity_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["card"],
                                     corner_radius=10, border_width=1,
                                     border_color=COLORS["border"])
        activity_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_rowconfigure(2, weight=1)
        
        activity_title = ctk.CTkLabel(activity_frame, text="Recent Activity",
                                     font=ctk.CTkFont(size=16, weight="bold"))
        activity_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        self.activity_list = ctk.CTkScrollableFrame(activity_frame, fg_color="transparent")
        self.activity_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def _update_dashboard(self):
        """Update dashboard with current data."""
        try:
            # Get stats
            reports = self._get_reports()
            screenshots = self._get_screenshots()
            
            today = datetime.now().strftime("%Y-%m-%d")
            today_reports = [r for r in reports if r["date"] == today]
            
            # Update stat cards
            self.stat_cards["reports"].configure(text=str(len(reports)))
            self.stat_cards["screenshots"].configure(text=str(len(screenshots)))
            self.stat_cards["today"].configure(text=str(len(today_reports)))
            
            # Calculate data size
            total_size = 0
            for root, dirs, files in os.walk(config.DATA_DIR):
                for f in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
            size_mb = total_size / (1024 * 1024)
            self.stat_cards["size"].configure(text=f"{size_mb:.1f} MB")
            
            # Update activity list
            for widget in self.activity_list.winfo_children():
                widget.destroy()
            
            if not reports:
                empty = ctk.CTkLabel(self.activity_list, text="No activity yet. Reports will appear here every 15 minutes.",
                                    text_color=COLORS["dim"])
                empty.pack(pady=20)
            else:
                for r in reports[:10]:
                    item = ctk.CTkFrame(self.activity_list, fg_color=COLORS["hover"], corner_radius=6)
                    item.pack(fill="x", pady=2)
                    
                    info = ctk.CTkLabel(item, text=f"📄 Report: {r['date']} {r['time']}",
                                       font=ctk.CTkFont(size=12))
                    info.pack(side="left", padx=10, pady=8)
                    
                    size = ctk.CTkLabel(item, text=f"{r['size']/1024:.1f} KB",
                                       font=ctk.CTkFont(size=11),
                                       text_color=COLORS["dim"])
                    size.pack(side="right", padx=10)
            
            # Update status
            self._update_status()
        except Exception as e:
            log.error(f"Dashboard update error: {e}")
    
    # ============ Reports View ============
    def _show_reports(self):
        """Show the reports view."""
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(header, text="Reports",
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")
        
        gen_btn = ctk.CTkButton(header, text="📄 Generate Now", width=130,
                               command=self._generate_report)
        gen_btn.pack(side="right", padx=(0, 10))
        
        refresh_btn = ctk.CTkButton(header, text="🔄 Refresh", width=100,
                                   command=self._load_reports)
        refresh_btn.pack(side="right")
        
        # Reports list
        self.reports_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.reports_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self._load_reports()
    
    def _load_reports(self):
        """Load and display reports."""
        for widget in self.reports_frame.winfo_children():
            widget.destroy()
        
        self.reports = self._get_reports()
        
        if not self.reports:
            empty = ctk.CTkLabel(self.reports_frame, text="No reports generated yet.",
                                text_color=COLORS["dim"], font=ctk.CTkFont(size=14))
            empty.pack(pady=40)
            return
        
        for r in self.reports:
            item = ctk.CTkFrame(self.reports_frame, fg_color=COLORS["card"],
                               corner_radius=8, border_width=1, border_color=COLORS["border"])
            item.pack(fill="x", pady=3)
            
            info_frame = ctk.CTkFrame(item, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            
            name = ctk.CTkLabel(info_frame, text=f"📄 {r['name']}",
                               font=ctk.CTkFont(size=13, weight="bold"))
            name.pack(anchor="w")
            
            meta = ctk.CTkLabel(info_frame, text=f"Date: {r['date']}  Time: {r['time']}  Size: {r['size']/1024:.1f} KB",
                               font=ctk.CTkFont(size=11),
                               text_color=COLORS["dim"])
            meta.pack(anchor="w", pady=(2, 0))
            
            view_btn = ctk.CTkButton(item, text="View", width=70,
                                    command=lambda r=r: self._view_report(r))
            view_btn.pack(side="right", padx=10)
    
    def _view_report(self, report):
        """View a report in a new window."""
        try:
            filepath = config.DOCS_DIR / report["name"]
            if not filepath.exists():
                return
            
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Create viewer window
            viewer = ctk.CTkToplevel(self)
            viewer.title(f"Report: {report['name']}")
            viewer.geometry("800x600")
            
            text = ctk.CTkTextbox(viewer, wrap="word", font=ctk.CTkFont(size=12))
            text.pack(fill="both", expand=True, padx=10, pady=10)
            text.insert("1.0", content)
            text.configure(state="disabled")
        except Exception as e:
            log.error(f"Error viewing report: {e}")
    
    # ============ Screenshots View ============
    def _show_screenshots(self):
        """Show the screenshots view."""
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(header, text="Screenshots",
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(header, text="🔄 Refresh", width=100,
                                   command=self._load_screenshots)
        refresh_btn.pack(side="right")
        
        # Screenshots grid
        self.screenshots_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.screenshots_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self._load_screenshots()
    
    def _load_screenshots(self):
        """Load and display screenshots."""
        for widget in self.screenshots_frame.winfo_children():
            widget.destroy()
        
        self.screenshots = self._get_screenshots()
        
        if not self.screenshots:
            empty = ctk.CTkLabel(self.screenshots_frame, text="No screenshots captured yet.",
                                text_color=COLORS["dim"], font=ctk.CTkFont(size=14))
            empty.pack(pady=40)
            return
        
        # Grid layout
        cols = 3
        for i, s in enumerate(self.screenshots[:30]):
            row = i // cols
            col = i % cols
            
            item = ctk.CTkFrame(self.screenshots_frame, fg_color=COLORS["card"],
                               corner_radius=8, border_width=1, border_color=COLORS["border"])
            item.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Load thumbnail
            try:
                img_path = config.SCREENSHOTS_DIR / s["name"]
                img = Image.open(img_path)
                img.thumbnail((250, 150))
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 150))
                
                img_label = ctk.CTkLabel(item, text="", image=photo)
                img_label.pack(padx=5, pady=(5, 0))
            except Exception:
                img_label = ctk.CTkLabel(item, text="📸", font=ctk.CTkFont(size=40))
                img_label.pack(pady=20)
            
            info = ctk.CTkLabel(item, text=f"{s['date']} {s['time']}",
                               font=ctk.CTkFont(size=11),
                               text_color=COLORS["dim"])
            info.pack(pady=(5, 5))
            
            view_btn = ctk.CTkButton(item, text="View Full", width=80, height=25,
                                    command=lambda s=s: self._view_screenshot(s))
            view_btn.pack(pady=(0, 8))
    
    def _view_screenshot(self, screenshot):
        """View a screenshot in a new window."""
        try:
            img_path = config.SCREENSHOTS_DIR / screenshot["name"]
            img = Image.open(img_path)
            
            # Resize to fit screen
            max_w, max_h = 1000, 700
            ratio = min(max_w / img.width, max_h / img.height, 1.0)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            
            viewer = ctk.CTkToplevel(self)
            viewer.title(f"Screenshot: {screenshot['name']}")
            viewer.geometry(f"{new_size[0]+20}x{new_size[1]+40}")
            
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=new_size)
            label = ctk.CTkLabel(viewer, text="", image=photo)
            label.pack(padx=10, pady=10)
        except Exception as e:
            log.error(f"Error viewing screenshot: {e}")
    
    # ============ Raw Data View ============
    def _show_raw(self):
        """Show the raw data view."""
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(header, text="Raw Data",
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(header, text="🔄 Refresh", width=100,
                                   command=self._load_raw)
        refresh_btn.pack(side="right")
        
        self.raw_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.raw_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self._load_raw()
    
    def _load_raw(self):
        """Load and display raw data files."""
        for widget in self.raw_frame.winfo_children():
            widget.destroy()
        
        self.raw_files = self._get_raw_files()
        
        if not self.raw_files:
            empty = ctk.CTkLabel(self.raw_frame, text="No raw data files.",
                                text_color=COLORS["dim"], font=ctk.CTkFont(size=14))
            empty.pack(pady=40)
            return
        
        for f in self.raw_files:
            item = ctk.CTkFrame(self.raw_frame, fg_color=COLORS["card"],
                               corner_radius=8, border_width=1, border_color=COLORS["border"])
            item.pack(fill="x", pady=3)
            
            info_frame = ctk.CTkFrame(item, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            
            name = ctk.CTkLabel(info_frame, text=f"📁 {f['name']}",
                               font=ctk.CTkFont(size=13, weight="bold"))
            name.pack(anchor="w")
            
            meta = ctk.CTkLabel(info_frame, text=f"Size: {f['size']/1024:.1f} KB  Modified: {f['modified']}",
                               font=ctk.CTkFont(size=11),
                               text_color=COLORS["dim"])
            meta.pack(anchor="w", pady=(2, 0))
            
            view_btn = ctk.CTkButton(item, text="View", width=70,
                                    command=lambda f=f: self._view_raw(f))
            view_btn.pack(side="right", padx=10)
    
    def _view_raw(self, raw_file):
        """View raw data in a new window."""
        try:
            filepath = config.RAW_DIR / raw_file["name"]
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            viewer = ctk.CTkToplevel(self)
            viewer.title(f"Raw Data: {raw_file['name']}")
            viewer.geometry("800x600")
            
            text = ctk.CTkTextbox(viewer, wrap="word", font=ctk.CTkFont(size=11))
            text.pack(fill="both", expand=True, padx=10, pady=10)
            text.insert("1.0", json.dumps(data, indent=2, default=str))
            text.configure(state="disabled")
        except Exception as e:
            log.error(f"Error viewing raw data: {e}")
    
    # ============ Processes View ============
    def _show_processes(self):
        """Show the processes view."""
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(header, text="Running Processes",
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(header, text="🔄 Refresh", width=100,
                                   command=self._load_processes)
        refresh_btn.pack(side="right")
        
        self.processes_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.processes_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self._load_processes()
    
    def _load_processes(self):
        """Load and display running processes."""
        for widget in self.processes_frame.winfo_children():
            widget.destroy()
        
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    pinfo = proc.info
                    processes.append({
                        "pid": pinfo["pid"],
                        "name": pinfo["name"],
                        "cpu": round(pinfo["cpu_percent"] or 0, 1),
                        "memory": round(pinfo["memory_percent"] or 0, 1),
                    })
                except:
                    continue
            processes.sort(key=lambda x: -x["cpu"])
            self.processes = processes[:50]
        except Exception as e:
            self.processes = []
        
        if not self.processes:
            empty = ctk.CTkLabel(self.processes_frame, text="No processes found.",
                                text_color=COLORS["dim"], font=ctk.CTkFont(size=14))
            empty.pack(pady=40)
            return
        
        # Header
        header_row = ctk.CTkFrame(self.processes_frame, fg_color=COLORS["card"])
        header_row.pack(fill="x", pady=(0, 5))
        
        for i, col in enumerate(["PID", "Process", "CPU %", "Memory %"]):
            label = ctk.CTkLabel(header_row, text=col, font=ctk.CTkFont(size=12, weight="bold"),
                                text_color=COLORS["dim"], width=150)
            label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        for p in self.processes:
            row = ctk.CTkFrame(self.processes_frame, fg_color=COLORS["hover"], corner_radius=4)
            row.pack(fill="x", pady=1)
            
            pid = ctk.CTkLabel(row, text=str(p["pid"]), font=ctk.CTkFont(size=12), width=150)
            pid.grid(row=0, column=0, padx=5, pady=3, sticky="w")
            
            name = ctk.CTkLabel(row, text=p["name"], font=ctk.CTkFont(size=12), width=150)
            name.grid(row=0, column=1, padx=5, pady=3, sticky="w")
            
            cpu = ctk.CTkLabel(row, text=f"{p['cpu']}%", font=ctk.CTkFont(size=12), width=150)
            cpu.grid(row=0, column=2, padx=5, pady=3, sticky="w")
            
            mem = ctk.CTkLabel(row, text=f"{p['memory']}%", font=ctk.CTkFont(size=12), width=150)
            mem.grid(row=0, column=3, padx=5, pady=3, sticky="w")
    
    # ============ Network View ============
    def _show_network(self):
        """Show the network view."""
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(header, text="Network Connections",
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(header, text="🔄 Refresh", width=100,
                                   command=self._load_network)
        refresh_btn.pack(side="right")
        
        self.network_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.network_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self._load_network()
    
    def _load_network(self):
        """Load and display network connections."""
        for widget in self.network_frame.winfo_children():
            widget.destroy()
        
        try:
            import psutil
            connections = []
            for conn in psutil.net_connections(kind="inet"):
                try:
                    if conn.status == "ESTABLISHED" and conn.raddr:
                        connections.append({
                            "pid": conn.pid,
                            "local": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                            "remote": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                            "status": conn.status,
                        })
                except:
                    continue
            self.network = connections[:50]
        except Exception as e:
            self.network = []
        
        if not self.network:
            empty = ctk.CTkLabel(self.network_frame, text="No active connections.",
                                text_color=COLORS["dim"], font=ctk.CTkFont(size=14))
            empty.pack(pady=40)
            return
        
        # Header
        header_row = ctk.CTkFrame(self.network_frame, fg_color=COLORS["card"])
        header_row.pack(fill="x", pady=(0, 5))
        
        for i, col in enumerate(["PID", "Local", "Remote", "Status"]):
            label = ctk.CTkLabel(header_row, text=col, font=ctk.CTkFont(size=12, weight="bold"),
                                text_color=COLORS["dim"], width=200)
            label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        for c in self.network:
            row = ctk.CTkFrame(self.network_frame, fg_color=COLORS["hover"], corner_radius=4)
            row.pack(fill="x", pady=1)
            
            pid = ctk.CTkLabel(row, text=str(c.get("pid", "-")), font=ctk.CTkFont(size=12), width=200)
            pid.grid(row=0, column=0, padx=5, pady=3, sticky="w")
            
            local = ctk.CTkLabel(row, text=c.get("local", ""), font=ctk.CTkFont(size=12), width=200)
            local.grid(row=0, column=1, padx=5, pady=3, sticky="w")
            
            remote = ctk.CTkLabel(row, text=c.get("remote", ""), font=ctk.CTkFont(size=12), width=200)
            remote.grid(row=0, column=2, padx=5, pady=3, sticky="w")
            
            status = ctk.CTkLabel(row, text=c.get("status", ""), font=ctk.CTkFont(size=12), width=200)
            status.grid(row=0, column=3, padx=5, pady=3, sticky="w")
    
    # ============ Logs View ============
    def _show_logs(self):
        """Show the logs view."""
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(header, text="Logs",
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(header, text="🔄 Refresh", width=100,
                                   command=self._load_logs)
        refresh_btn.pack(side="right")
        
        self.logs_text = ctk.CTkTextbox(self.main_frame, wrap="word",
                                       font=ctk.CTkFont(size=11, family="Consolas"))
        self.logs_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self._load_logs()
    
    def _load_logs(self):
        """Load and display logs."""
        log_file = config.LOGS_DIR / "tracker.log"
        if not log_file.exists():
            self.logs_text.delete("1.0", "end")
            self.logs_text.insert("1.0", "No logs available.")
            return
        
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            self.logs = lines[-200:]
            
            self.logs_text.delete("1.0", "end")
            self.logs_text.insert("1.0", "".join(self.logs))
            self.logs_text.see("end")
        except Exception as e:
            self.logs_text.delete("1.0", "end")
            self.logs_text.insert("1.0", f"Error loading logs: {e}")
    
    # ============ Settings View ============
    def _show_settings(self):
        """Show the settings/control view."""
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(header, text="Control Center",
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")
        
        # Control panel
        control_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["card"],
                                    corner_radius=10, border_width=1, border_color=COLORS["border"])
        control_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        control_title = ctk.CTkLabel(control_frame, text="Tracker Control",
                                    font=ctk.CTkFont(size=16, weight="bold"))
        control_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        btn_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.start_btn = ctk.CTkButton(btn_frame, text="▶️ Start", width=100,
                                      fg_color=COLORS["green"], hover_color="#3d8b40",
                                      command=self._start_tracker)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(btn_frame, text="⏹️ Stop", width=100,
                                     fg_color=COLORS["red"], hover_color="#d32f2f",
                                     command=self._stop_tracker)
        self.stop_btn.pack(side="left", padx=5)
        
        self.restart_btn = ctk.CTkButton(btn_frame, text="🔄 Restart", width=100,
                                        fg_color=COLORS["yellow"], hover_color="#d4a000",
                                        text_color="#333",
                                        command=self._restart_tracker)
        self.restart_btn.pack(side="left", padx=5)
        
        gen_btn = ctk.CTkButton(btn_frame, text="📄 Generate Report", width=140,
                               command=self._generate_report)
        gen_btn.pack(side="left", padx=5)
        
        cleanup_btn = ctk.CTkButton(btn_frame, text="🧹 Run Cleanup", width=120,
                                   command=self._run_cleanup)
        cleanup_btn.pack(side="left", padx=5)
        
        # Settings panel
        settings_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["card"],
                                     corner_radius=10, border_width=1, border_color=COLORS["border"])
        settings_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        settings_title = ctk.CTkLabel(settings_frame, text="Configuration",
                                     font=ctk.CTkFont(size=16, weight="bold"))
        settings_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Interval settings
        interval_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        interval_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(interval_frame, text="Report Interval (minutes):",
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        
        self.interval_var = ctk.StringVar(value=str(config.INTERVAL_MINUTES))
        interval_entry = ctk.CTkEntry(interval_frame, textvariable=self.interval_var, width=80)
        interval_entry.pack(side="left")
        
        ctk.CTkLabel(interval_frame, text="Screenshot Interval (seconds):",
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=(20, 10))
        
        self.screenshot_interval_var = ctk.StringVar(value=str(config.SCREENSHOT_INTERVAL_SECONDS))
        screenshot_entry = ctk.CTkEntry(interval_frame, textvariable=self.screenshot_interval_var, width=80)
        screenshot_entry.pack(side="left")
        
        ctk.CTkLabel(interval_frame, text="Retention (days):",
                    font=ctk.CTkFont(size=12)).pack(side="left", padx=(20, 10))
        
        self.retention_var = ctk.StringVar(value=str(config.RETENTION_DAYS))
        retention_entry = ctk.CTkEntry(interval_frame, textvariable=self.retention_var, width=80)
        retention_entry.pack(side="left")
        
        # Toggle settings
        toggles_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        self.toggles = {}
        toggle_items = [
            ("screenshots", "Screenshots", "Capture screen images"),
            ("keyboard", "Keyboard Tracking", "Log keystrokes"),
            ("mouse", "Mouse Tracking", "Log mouse activity"),
            ("process", "Process Monitoring", "Track running processes"),
            ("network", "Network Monitoring", "Track network connections"),
            ("window", "Window Tracking", "Track active windows"),
        ]
        
        for i, (key, label, desc) in enumerate(toggle_items):
            row = i // 2
            col = i % 2
            
            toggle_frame = ctk.CTkFrame(toggles_frame, fg_color=COLORS["hover"], corner_radius=6)
            toggle_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            toggles_frame.grid_columnconfigure(col, weight=1)
            
            text_frame = ctk.CTkFrame(toggle_frame, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)
            
            ctk.CTkLabel(text_frame, text=label, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(text_frame, text=desc, font=ctk.CTkFont(size=10),
                        text_color=COLORS["dim"]).pack(anchor="w")
            
            var = ctk.BooleanVar(value=getattr(config, {
                "screenshots": "SCREENSHOT_ENABLED",
                "keyboard": "KEYBOARD_ENABLED",
                "mouse": "MOUSE_ENABLED",
                "process": "PROCESS_ENABLED",
                "network": "NETWORK_ENABLED",
                "window": "WINDOW_ENABLED",
            }[key]))
            self.toggles[key] = var
            
            switch = ctk.CTkSwitch(toggle_frame, text="", variable=var, width=40)
            switch.pack(side="right", padx=10)
        
        # Save button
        save_btn = ctk.CTkButton(settings_frame, text="💾 Save Configuration", width=180,
                                fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                command=self._save_config)
        save_btn.pack(pady=15)
    
    def _save_config(self):
        """Save configuration settings."""
        try:
            # Update config
            config.INTERVAL_MINUTES = int(self.interval_var.get())
            config.SCREENSHOT_INTERVAL_SECONDS = int(self.screenshot_interval_var.get())
            config.RETENTION_DAYS = int(self.retention_var.get())
            
            config.SCREENSHOT_ENABLED = self.toggles["screenshots"].get()
            config.KEYBOARD_ENABLED = self.toggles["keyboard"].get()
            config.MOUSE_ENABLED = self.toggles["mouse"].get()
            config.PROCESS_ENABLED = self.toggles["process"].get()
            config.NETWORK_ENABLED = self.toggles["network"].get()
            config.WINDOW_ENABLED = self.toggles["window"].get()
            
            config.save_config()
            log.info("Configuration saved from desktop app")
            
            # Show success
            self._show_message("Configuration saved successfully!", "success")
        except Exception as e:
            self._show_message(f"Error saving config: {e}", "error")
    
    # ============ Tracker Control ============
    def _start_tracker(self):
        """Start the tracker."""
        try:
            from tracker.main import DailyTracker
            
            if self.tracker and self.tracker._running:
                self._show_message("Tracker is already running", "info")
                return
            
            self.tracker = DailyTracker()
            self.tracker.start()
            self._update_status()
            self._show_message("Tracker started", "success")
        except Exception as e:
            self._show_message(f"Error starting tracker: {e}", "error")
    
    def _stop_tracker(self):
        """Stop the tracker."""
        try:
            if self.tracker and self.tracker._running:
                self.tracker.stop()
                self._update_status()
                self._show_message("Tracker stopped", "success")
            else:
                self._show_message("Tracker is not running", "info")
        except Exception as e:
            self._show_message(f"Error stopping tracker: {e}", "error")
    
    def _restart_tracker(self):
        """Restart the tracker."""
        try:
            from tracker.main import DailyTracker
            
            if self.tracker and self.tracker._running:
                self.tracker.stop()
            
            self.tracker = DailyTracker()
            self.tracker.start()
            self._update_status()
            self._show_message("Tracker restarted", "success")
        except Exception as e:
            self._show_message(f"Error restarting tracker: {e}", "error")
    
    def _generate_report(self):
        """Generate a report manually."""
        try:
            if not self.tracker or not self.tracker._running:
                self._show_message("Tracker is not running. Start it first.", "error")
                return
            
            report_path = self.tracker._generate_report(datetime.now())
            if report_path:
                self._show_message(f"Report generated: {report_path.name}", "success")
                self._load_reports()
            else:
                self._show_message("Failed to generate report", "error")
        except Exception as e:
            self._show_message(f"Error generating report: {e}", "error")
    
    def _run_cleanup(self):
        """Run cleanup manually."""
        try:
            from tracker.cleanup import cleanup_old_files
            removed = cleanup_old_files()
            self._show_message(f"Cleanup complete. Removed {removed} files", "success")
        except Exception as e:
            self._show_message(f"Error running cleanup: {e}", "error")
    
    # ============ Helper Methods ============
    def _get_reports(self):
        """Get list of reports."""
        reports = []
        docs_dir = config.DOCS_DIR
        if docs_dir.exists():
            for f in sorted(docs_dir.glob("report_*.md"), reverse=True):
                try:
                    stats = f.stat()
                    reports.append({
                        "name": f.name,
                        "size": stats.st_size,
                        "modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "date": f.name.replace("report_", "").replace(".md", "").split("_")[0],
                        "time": f.name.replace("report_", "").replace(".md", "").split("_")[1],
                    })
                except:
                    continue
        return reports
    
    def _get_screenshots(self):
        """Get list of screenshots."""
        screenshots = []
        shots_dir = config.SCREENSHOTS_DIR
        if shots_dir.exists():
            for f in sorted(shots_dir.glob("*.jpg"), reverse=True):
                try:
                    stats = f.stat()
                    screenshots.append({
                        "name": f.name,
                        "size": stats.st_size,
                        "date": f.name[:8],
                        "time": f"{f.name[8:10]}:{f.name[10:12]}:{f.name[12:14]}",
                    })
                except:
                    continue
        return screenshots
    
    def _get_raw_files(self):
        """Get list of raw data files."""
        raw_files = []
        raw_dir = config.RAW_DIR
        if raw_dir.exists():
            for f in sorted(raw_dir.glob("raw_*.json"), reverse=True):
                try:
                    stats = f.stat()
                    raw_files.append({
                        "name": f.name,
                        "size": stats.st_size,
                        "modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    })
                except:
                    continue
        return raw_files
    
    def _update_status(self):
        """Update the status indicator."""
        running = self.tracker and self.tracker._running
        if running:
            self.status_dot.configure(text_color=COLORS["green"])
            self.status_label.configure(text="Running", text_color=COLORS["green"])
        else:
            self.status_dot.configure(text_color=COLORS["red"])
            self.status_label.configure(text="Stopped", text_color=COLORS["dim"])
    
    def _show_message(self, message, type="info"):
        """Show a message dialog."""
        colors = {
            "success": COLORS["green"],
            "error": COLORS["red"],
            "info": COLORS["accent"],
        }
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Daily Tracker")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(dialog, text=message, font=ctk.CTkFont(size=14),
                            wraplength=350)
        label.pack(pady=30)
        
        ok_btn = ctk.CTkButton(dialog, text="OK", width=100,
                              fg_color=colors.get(type, COLORS["accent"]),
                              command=dialog.destroy)
        ok_btn.pack(pady=10)
    
    def _start_refresh(self):
        """Start background refresh timer."""
        def refresh():
            try:
                self.refresh_all()
            except:
                pass
            self.after(30000, refresh)  # Refresh every 30 seconds
        
        self.after(30000, refresh)
    
    def refresh_all(self):
        """Refresh all data."""
        try:
            if self.current_view == "dashboard":
                self._update_dashboard()
            elif self.current_view == "reports":
                self._load_reports()
            elif self.current_view == "screenshots":
                self._load_screenshots()
            elif self.current_view == "raw":
                self._load_raw()
            elif self.current_view == "processes":
                self._load_processes()
            elif self.current_view == "network":
                self._load_network()
            elif self.current_view == "logs":
                self._load_logs()
            
            self._update_status()
        except Exception as e:
            log.error(f"Refresh error: {e}")


def main():
    """Main entry point."""
    app = TrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()