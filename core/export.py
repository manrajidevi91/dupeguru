# Created By: Virgil Dupras
# Created On: 2006/09/16
# Copyright 2015 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import os.path as op
from tempfile import mkdtemp
import csv
import json
from datetime import datetime

# Yes, this is a very low-tech solution, but at least it doesn't have all these annoying dependency
# and resource problems.

MAIN_TEMPLATE = """
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Strict//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta content="text/html; charset=utf-8" http-equiv="Content-Type"/>
        <title>dupeGuru Results</title>
        <style type="text/css">
BODY
{
    background-color:white;
}

BODY,A,P,UL,TABLE,TR,TD
{
    font-family:Tahoma,Arial,sans-serif;
    font-size:10pt;
    color: #4477AA;
}

TABLE
{
    background-color: #225588;
    margin-left: auto;
    margin-right: auto;
    width: 90%;
}

TR
{
    background-color: white;
}

TH
{
    font-weight: bold;
    color: black;
    background-color: #C8D6E5;
}

TH TD
{
    color:black;
}

TD
{
    padding-left: 2pt;
}

TD.rightelem
{
    text-align:right;
    /*padding-left:0pt;*/
    padding-right: 2pt;
    width: 17%;
}

TD.indented
{
    padding-left: 12pt;
}

H1
{
    font-family:&quot;Courier New&quot;,monospace;
    color:#6699CC;
    font-size:18pt;
    color:#6da500;
    border-color: #70A0CF;
    border-width: 1pt;
    border-style: solid;
    margin-top:   16pt;
    margin-left:  5%;
    margin-right: 5%;
    padding-top:  2pt;
    padding-bottom:2pt;
    text-align:   center;
}
</style>
</head>
<body>
<h1>dupeGuru Results</h1>
<table>
<tr>$colheaders</tr>
$rows
</table>
</body>
</html>
"""

COLHEADERS_TEMPLATE = "<th>{name}</th>"

ROW_TEMPLATE = """
<tr>
    <td class="{indented}">{filename}</td>{cells}
</tr>
"""

CELL_TEMPLATE = """<td>{value}</td>"""


def export_to_xhtml(colnames, rows):
    # a row is a list of values with the first value being a flag indicating if the row should be indented
    if rows:
        assert len(rows[0]) == len(colnames) + 1  # + 1 is for the "indented" flag
    colheaders = "".join(COLHEADERS_TEMPLATE.format(name=name) for name in colnames)
    rendered_rows = []
    previous_group_id = None
    for row in rows:
        # [2:] is to remove the indented flag + filename
        if row[0] != previous_group_id:
            # We've just changed dupe group, which means that this dupe is a ref. We don't indent it.
            indented = ""
        else:
            indented = "indented"
        filename = row[1]
        cells = "".join(CELL_TEMPLATE.format(value=value) for value in row[2:])
        rendered_rows.append(ROW_TEMPLATE.format(indented=indented, filename=filename, cells=cells))
        previous_group_id = row[0]
    rendered_rows = "".join(rendered_rows)
    # The main template can't use format because the css code uses {}
    content = MAIN_TEMPLATE.replace("$colheaders", colheaders).replace("$rows", rendered_rows)
    folder = mkdtemp()
    destpath = op.join(folder, "export.htm")
    fp = open(destpath, "wt", encoding="utf-8")
    fp.write(content)
    fp.close()
    return destpath


def export_to_csv(dest, colnames, rows):
    writer = csv.writer(open(dest, "wt", encoding="utf-8"))
    writer.writerow(["Group ID"] + colnames)
    for row in rows:
        writer.writerow(row)


def export_to_json(dest, colnames, rows, metadata=None):
    """Export results to JSON format.
    
    Args:
        dest: Destination file path
        colnames: List of column names
        rows: List of row data (group_id, filename, values...)
        metadata: Optional metadata dict (scan_time, directories, etc.)
    
    Returns:
        Path to the exported file
    """
    export_data = {
        "export_time": datetime.now().isoformat(),
        "format_version": "1.0",
        "columns": colnames,
        "groups": [],
    }
    
    # Add metadata if provided
    if metadata:
        export_data["metadata"] = metadata
    
    # Group rows by group_id
    current_group = None
    for row in rows:
        group_id = row[0]
        filename = row[1]
        values = row[2:]
        
        # Create dict for this row
        row_dict = dict(zip(colnames, values))
        row_dict["filename"] = filename
        
        if group_id != current_group:
            # New group
            export_data["groups"].append({
                "group_id": group_id,
                "files": [row_dict]
            })
            current_group = group_id
        else:
            # Add to existing group
            export_data["groups"][-1]["files"].append(row_dict)
    
    # Write to file
    with open(dest, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    return dest


def generate_summary_report(results, app_mode="standard"):
    """Generate a summary report of scan results.
    
    Args:
        results: Results object with duplicate groups
        app_mode: App mode (standard/music/picture)
    
    Returns:
        Dict with summary statistics
    """
    groups = results.groups
    total_groups = len(groups)
    total_duplicates = sum(len(g.dupes) for g in groups)
    marked_duplicates = results.mark_count
    
    # Calculate space statistics
    total_size = sum(g.ref.size for g in groups if hasattr(g.ref, 'size'))
    marked_size = 0
    space_saved = 0
    
    for group in groups:
        for dupe in group.dupes:
            if results.is_marked(dupe) and hasattr(dupe, 'size'):
                marked_size += dupe.size
        
        # Space that could be saved by removing duplicates
        ref_size = group.ref.size if hasattr(group.ref, 'size') else 0
        dupe_sizes = sum(d.size for d in group.dupes if hasattr(d, 'size'))
        space_saved += dupe_sizes - ref_size
    
    # Calculate similarity statistics
    similarities = [g.percentage for g in groups if hasattr(g, 'percentage')]
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0
    min_similarity = min(similarities) if similarities else 0
    max_similarity = max(similarities) if similarities else 0
    
    # Mode-specific statistics
    mode_stats = {}
    if app_mode == "picture":
        # Count by resolution
        resolution_counts = {}
        for group in groups:
            if hasattr(group.ref, 'dimensions') and group.ref.dimensions:
                res = f"{group.ref.dimensions[0]}x{group.ref.dimensions[1]}"
                resolution_counts[res] = resolution_counts.get(res, 0) + 1
        
        mode_stats = {
            "resolution_distribution": resolution_counts,
        }
    
    return {
        "scan_time": datetime.now().isoformat(),
        "app_mode": app_mode,
        "total_groups": total_groups,
        "total_duplicates": total_duplicates,
        "marked_duplicates": marked_duplicates,
        "unmarked_duplicates": total_duplicates - marked_duplicates,
        "total_size_bytes": total_size,
        "marked_size_bytes": marked_size,
        "space_saved_bytes": space_saved,
        "average_similarity": round(avg_similarity, 2),
        "min_similarity": round(min_similarity, 2),
        "max_similarity": round(max_similarity, 2),
        "mode_specific": mode_stats,
    }


def export_summary_report(dest, summary_data):
    """Export summary report to JSON file.
    
    Args:
        dest: Destination file path
        summary_data: Summary data dict from generate_summary_report()
    
    Returns:
        Path to the exported file
    """
    with open(dest, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    return dest
