import os
import json
import logging
import shutil
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
from send2trash import send2trash

# dupeGuru core imports
from core import fs, scanner, engine
from core.pe.scanner import ScannerPE
from core.pe.photo import PhotoFile

app = Flask(__name__)

@app.route('/api/browse_os', methods=['GET'])
def browse_os_directory():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder_path = filedialog.askdirectory(parent=root, title="Select Folder for dupeGuru")
        root.destroy()
        
        if folder_path:
            return jsonify({"status": "success", "path": os.path.abspath(folder_path)})
        return jsonify({"status": "cancel"})
    except Exception as e:
        logger.error(f"Error opening native browse: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for the scan session
class ScanSession:
    def __init__(self):
        self.folders = []
        self.results = [] # List of groups
        self.scan_type = scanner.ScanType.FUZZYBLOCK
        self.threshold = 95
        self.scanning = False
        self.appdata = Path(os.environ.get('APPDATA', '.')) / 'dupeguru-web'
        self.appdata.mkdir(parents=True, exist_ok=True)
        self.cache_path = str(self.appdata / 'cached_pictures.db')

session = ScanSession()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/folders', methods=['GET', 'POST', 'DELETE'])
def manage_folders():
    if request.method == 'POST':
        data = request.json
        folder_path = data.get('path')
        if folder_path and os.path.isdir(folder_path):
            if folder_path not in session.folders:
                session.folders.append(folder_path)
            return jsonify({"status": "success", "folders": session.folders})
        return jsonify({"status": "error", "message": "Invalid folder path"}), 400
    
    elif request.method == 'DELETE':
        data = request.json
        folder_path = data.get('path')
        if folder_path in session.folders:
            session.folders.remove(folder_path)
        return jsonify({"status": "success", "folders": session.folders})
    
    return jsonify({"folders": session.folders})

@app.route('/api/scan', methods=['POST'])
def run_scan():
    if not session.folders:
        return jsonify({"status": "error", "message": "No folders selected"}), 400
    
    session.scanning = True
    try:
        # 1. Collect files from folders
        all_files = []
        file_classes = [PhotoFile]
        
        for folder in session.folders:
            folder_path = Path(folder)
            for root, dirs, files in os.walk(folder_path):
                for name in files:
                    file_path = Path(root) / name
                    try:
                        f = fs.get_file(file_path, file_classes)
                        if f and PhotoFile.can_handle(file_path):
                            all_files.append(f)
                    except Exception as e:
                        logger.error(f"Error reading {file_path}: {e}")

        # 2. Run Scanner PE
        s = ScannerPE()
        s.scan_type = session.scan_type
        s.min_match_percentage = session.threshold
        s.cache_path = session.cache_path
        
        groups = s.get_dupe_groups(all_files)
        
        # 3. Format results for JSON
        session.results = []
        for i, group in enumerate(groups):
            group_data = {
                "id": i + 1,
                "ref": format_file(group.ref),
                "duplicates": [format_file(dupe, group) for dupe in group.dupes]
            }
            session.results.append(group_data)
            
        session.scanning = False
        return jsonify({"status": "success", "groups": session.results})
    
    except Exception as e:
        session.scanning = False
        logger.exception("Scan failed")
        return jsonify({"status": "error", "message": str(e)}), 500

def format_file(f, group=None):
    # Ensure metadata is read
    f._read_all_info()
    
    data = {
        "path": str(f.path),
        "name": f.name,
        "size": f.size,
        "folder": str(f.path.parent),
    }
    if hasattr(f, 'dimensions'):
        data["dimensions"] = f"{f.dimensions[0]} x {f.dimensions[1]}"
    
    if group:
        match = group.get_match_of(f)
        if match:
            data["percentage"] = match.percentage
            
    return data

@app.route('/api/image')
def get_image():
    path = request.args.get('path')
    if path and os.path.exists(path):
        return send_file(path)
    return "Not Found", 404

@app.route('/api/export_excel', methods=['POST'])
def export_excel():
    try:
        data = request.json
        groups = data.get('groups', [])
        
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
        from io import BytesIO
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Duplicate Report"
        
        # Headers
        headers = ["Group ID", "Retained Master File (Path)", "Deleted Duplicate File (Path)"]
        ws.append(headers)
        
        # Style headers
        header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for group in groups:
            group_id = group.get('group_id')
            master = group.get('master_path')
            dupes = group.get('duplicates', [])
            
            if not dupes:
                continue
                
            for dupe in dupes:
                ws.append([group_id, master, dupe])
        
        # Auto-adjust columns width
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except: pass
            ws.column_dimensions[column].width = min(max_length + 2, 100)

        out = BytesIO()
        wb.save(out)
        out.seek(0)
        
        return send_file(
            out,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='dupeGuru_Report.xlsx'
        )
    except Exception as e:
        logger.error(f"Excel export failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def delete_files():
    data = request.json
    file_paths = data.get('paths', [])
    success_count = 0
    errors = []
    
    for path in file_paths:
        try:
            if os.path.exists(path):
                send2trash(path)
                success_count += 1
        except Exception as e:
            errors.append({"path": path, "error": str(e)})
            
    return jsonify({"status": "success", "deleted": success_count, "errors": errors})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)
