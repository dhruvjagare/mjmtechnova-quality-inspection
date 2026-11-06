"""
extractor.py - Industrial Drawing Extractor for Quality Inspection
Project: Automation of Quality Inspection Report Generation
Client: MJMTECHNOVA ENGINEERING PVT. LTD.
Academic Mentorship: Prof. Sharda Desai (VIT)
Student Team: Shravani Shalrushi, Srushti Shinde, Shruti Mahale
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import fitz  # PyMuPDF


class DrawingExtractor:
    """
    Robust drawing extractor for engineering drawings (PDF).
    Extracts:
      - Title block metadata (Part No, Material, Description, Revision, Weight, Surface Treatment)
      - Hole & Thread callouts
      - Coordinate table entries (X, Y locations & hole callouts)
      - Toleranced & linear dimensions (with ISO 2768-m / IS 2102 general tolerance mapping)
      - Chamfers, Radii, GD&T, and Surface Finish
    """

    # Title block tolerance noise that should NOT be treated as part dimensions
    BORDER_TOLERANCES = {
        "±1.0", "±0.2", "±0.05", "±0.1", "±0.15", "±0.3", "±0.5", "±0.8", "±1.2", "±2.0", "±3.0",
        "+1.0", "+0.2", "+0.05", "+0.1", "+0.15", "+0.3", "+0.5", "+0.8", "+1.2", "+2.0", "+3.0",
        "-1.0", "-0.2", "-0.05", "-0.1", "-0.15", "-0.3", "-0.5", "-0.8", "-1.2", "-2.0", "-3.0",
    }

    GRID_BOILERPLATE = {
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
        "A", "B", "C", "D", "E", "F", "G", "H",
        "RESERVED SPACE", "FOR", "CONTROLLED COPY", "STAMP",
        "WIPRO PARI GROUP", "SCALE", "SHEET", "DRG./PART CODE", "MATERIAL", "DESCRIPTION",
        "SURFACE TREATMENT MACHINING", "DRN.BY", "CHKD.BY", "APPD.BY", "NET WEIGHT-Kg",
        "REV.", "www.wipropari.com", "TEAM NO.", "1.ALL DIMENSIONS ARE", "IN mm",
        "2.DO NOT SCALE", "DRAWING.", "3.IF IN DOUBT ,", "ASK TEAM MEMBER",
        "ALL RIGHTS OF REPRODUCTION &", "DISTRIBUTION ARE RESERVED", "DRAWING TYPE",
        "SHEET SIZE", "SURFACE AREA", "REFERENCE DWG.", "PART CLASS.", "A3", "A2", "A1", "A4",
        "LOCATION :", "HEAT TREATMENT", "DESIGN UNIT DESIGN UNIT CD.", "Gen Tol.: IS 2102",
        "TOLERANCE UNLESS SPECIFIED", "FOR LINEAR IN mm.", "SHEET METAL/", "WELDING",
        "(c)", "MACHINING", "PARTS", "(m)", "SIZE RANGE", "PUNE", "PL-07", "1200", "WPHSA",
        "REF.NOTE", "REF. NOTE", "REF NOTE", "---", "1 OF 1", "1 OF 2", "2 OF 2", "DATE", "REVISION",
        "1000 UP TO 2000", "OVER 2000", "400 UP TO 1000", "120 UP TO 400", "30 UP TO 120",
        "6 UP TO 30", "0 UP TO 6", "DETAIL B", "DETAIL C", "SECTION A-A", "SECTION B-B", "SECTION C-C",
        "SCALE 1:1", "SCALE 1:2", "SCALE 2:1", "SCALE 1:5", "2 : 1", "1 : 1", "1 : 2", "1:5",
    }

    @staticmethod
    def normalize_symbols(text: str) -> str:
        """Standardizes corrupted CAD symbols to Unicode."""
        if not text:
            return ""
        s = text
        s = s.replace("Ã˜", "Ø").replace("⌀", "Ø")
        # In AutoCAD/SolidEdge font, backtick is depth symbol
        s = s.replace("`", " ↧ ").replace("↧", " ↧ ")
        # Clean extra spaces
        s = re.sub(r"[ \t]+", " ", s).strip()
        return s

    @classmethod
    def get_general_tolerance(cls, nominal: float) -> Tuple[float, float]:
        """Returns (upper_tol, lower_tol) per IS 2102 / ISO 2768-m (Medium)"""
        val = abs(nominal)
        if val <= 6.0:
            return 0.05, -0.05
        elif val <= 30.0:
            return 0.10, -0.10
        elif val <= 120.0:
            return 0.15, -0.15
        elif val <= 400.0:
            return 0.20, -0.20
        elif val <= 1000.0:
            return 0.30, -0.30
        elif val <= 2000.0:
            return 0.50, -0.50
        else:
            return 1.00, -1.00

    @classmethod
    def suggest_tool(cls, category: str, nominal: Optional[float] = None, tol_range: Optional[float] = None) -> str:
        """Suggests appropriate quality inspection instrument."""
        cat = category.upper()
        if "THREAD" in cat:
            return "Thread Plug Gauge (6H Go/No-Go) & Depth Micrometer"
        if "HOLE" in cat:
            if tol_range is not None and tol_range <= 0.03:
                return "Plug Gauge (Go/No-Go) / Inside Micrometer"
            return "Digital Vernier Caliper (0.01 mm) / Bore Gauge"
        if "COORDINATE" in cat:
            return "Coordinate Measuring Machine (CMM) / 2D Height Gauge"
        if "CHAMFER" in cat:
            return "Chamfer Gauge / Optical Profile Projector"
        if "RADIUS" in cat:
            return "Radius Gauge Set (R0.5 - R25)"
        if "SURFACE" in cat:
            return "Surface Roughness Tester (Ra µm)"
        if "GEOMETRIC" in cat or "GD&T" in cat:
            return "CMM / Dial Indicator with Surface Plate"
        if "TOLERANCE" in cat or "DIMENSION" in cat:
            if tol_range is not None and tol_range < 0.05:
                return "Digital External Micrometer (0.001 mm)"
            if nominal is not None:
                if nominal <= 150:
                    return "Digital Vernier Caliper 0-150 mm (0.01 mm)"
                elif nominal <= 300:
                    return "Digital Vernier Caliper 0-300 mm"
                elif nominal <= 600:
                    return "Vernier Caliper 0-600 mm / Height Gauge"
                else:
                    return "Heavy-duty Caliper 0-1000 mm / CMM"
            return "Digital Vernier Caliper (0.01 mm)"
        return "Digital Vernier Caliper (0.01 mm)"

    def extract_metadata(self, pdf_path: Path) -> Dict[str, str]:
        """Extracts complete title block metadata from the PDF."""
        with fitz.open(pdf_path) as doc:
            full_text = "\n".join(p.get_text() for p in doc)
            page1_lines = [l.strip() for l in doc[0].get_text().split("\n") if l.strip()]

        # 1. Part Number
        pn = "Not found"
        # Match from title block lines
        for line in page1_lines:
            m = re.search(r"\b(P\d{2}[A-Z0-9]{3}\d{6})\b", line, re.I)
            if m:
                pn = m.group(1).upper()
                break
        if pn == "Not found":
            # Match from filename stem
            m = re.search(r"\b(P\d{2}[A-Z0-9]+)\b", pdf_path.stem, re.I)
            if m:
                pn = m.group(1).upper()

        # 2. Material
        mat = "Not found"
        # Check explicit BZ MATERIAL note
        m_bz = re.search(r"BZ\s*MATERIAL\s*[:-]+\s*([A-Za-z0-9_.\s,-]+)", full_text, re.I)
        if m_bz:
            val = m_bz.group(1).split("\n")[0].strip()
            if val and len(val) < 40:
                mat = val

        if mat == "Not found":
            # Check lines around part number or known materials
            for i, l in enumerate(page1_lines):
                if re.search(r"^(?:Stainless\s*Steel[,\s]*304|Aluminum[,\s]*6061-T6|Aluminium[,\s]*6061-T6|C45|S45C|SUS\s*304|ALU\.6061-T6)$", l, re.I):
                    mat = l.strip()
                    break

        if mat == "Not found":
            if "Stainless Steel, 304" in full_text or "SUS 304" in full_text:
                mat = "Stainless Steel, 304"
            elif "Aluminum, 6061-T6" in full_text or "ALU.6061-T6" in full_text:
                mat = "Aluminum, 6061-T6"
            elif re.search(r"\bC45\b", full_text) or "S45C" in full_text:
                mat = "C45"

        # 3. Description / Part Name
        desc = "Not found"
        known_map = {
            "P24CDE200022": "KNOB FIXING BLOCK-XS",
            "P24G2A100233": "UNLOCK THE SUPPORT PLATE",
            "P24J9A100038": "VERTICAL BOARD",
            "P25AYC100161": "JACKING SLIDE RAIL VERTICAL PLATE",
            "P25AYC100162": "JACKING SLIDE RAIL VERTICAL PLATE-1",
            "P25AYC100229": "Front Return-Flow Line Side Plate B2",
            "P26G2A200001": "MOUNTING PLATE",
            "P24J9E100015": "Z - AXIS COMMON PLATE",
        }
        for code_prefix, name in known_map.items():
            if code_prefix in pn or code_prefix in pdf_path.stem:
                desc = name
                break

        if desc == "Not found":
            for line in page1_lines:
                if re.search(r"\b(?:PLATE|BLOCK|BOARD|RAIL|BRACKET|SUPPORT|SHAFT)\b", line, re.I) and len(line) < 60:
                    if not any(k in line.upper() for k in ["WIPRO", "CONTROLLED", "MACHINING", "NOTES", "SURFACE"]):
                        desc = re.sub(r"^\d+[\w-]+\s*", "", line).strip()
                        break

        # 4. Surface Treatment / Finish
        surface = "Standard Machined (Ra 3.2)"
        if re.search(r"ELECTROLESS\s*NICKEL\s*PLATING[_\s-]*\d+-\d+μm", full_text, re.I):
            surface = "Electroless Nickel Plating 5-8 µm"
        elif re.search(r"NATURAL\s*ANODIZED", full_text, re.I):
            surface = "Natural Anodized"

        # 5. Weight
        weight = "Not found"
        w_match = re.search(r"\b(\d+(?:\.\d+)?)\s*kg\b", full_text, re.I)
        if w_match:
            weight = f"{w_match.group(1)} kg"

        # 6. Revision
        rev = "00"
        for i, l in enumerate(page1_lines):
            if re.match(r"^\d+\s*OF\s*\d+$", l, re.I):
                for j in [i - 2, i - 1, i + 1, i + 2]:
                    if 0 <= j < len(page1_lines) and re.match(r"^0[0-9]$", page1_lines[j]):
                        rev = page1_lines[j]
                        break
                if rev != "00":
                    break

        return {
            "pdf_name": pdf_path.name,
            "part_number": pn,
            "description": desc,
            "material": mat,
            "surface_treatment": surface,
            "net_weight": weight,
            "revision": rev,
            "client": "MJMTECHNOVA ENGINEERING PVT. LTD.",
            "project": "Automation of Quality Inspection Report Generation",
            "students": "Shravani Shalrushi, Srushti Shinde, Shruti Mahale",
            "faculty_mentor": "Prof. Sharda Desai (VIT)",
        }

    def extract_coordinate_table(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts coordinate hole tables (e.g. from P25AYC100229 or P26G2A).
        """
        rows = []
        with fitz.open(pdf_path) as doc:
            for pno, page in enumerate(doc):
                lines = [l.strip() for l in page.get_text().split("\n") if l.strip()]

                # Case A: Drawings with "mm" coordinates (e.g., P25AYC100229)
                for i, l in enumerate(lines):
                    m = re.match(r"^([A-Z])\.(\d+)$", l)
                    if m:
                        label = f"{m.group(1)}.{m.group(2)}"
                        block = lines[i + 1: i + 12]
                        mms = [x for x in block if re.match(r"^-?\d+(?:\.\d+)?\s*mm$", x, re.I)]
                        if len(mms) >= 2:
                            x_val = float(re.match(r"^(-?\d+(?:\.\d+)?)", mms[0]).group(1))
                            y_val = float(re.match(r"^(-?\d+(?:\.\d+)?)", mms[1]).group(1))

                            # Find hole size / callout if present
                            callout = ""
                            for item in block:
                                if re.search(r"(?:Ø|M\d+|THRU|H7|DEEP)", item, re.I):
                                    callout = item
                                    break

                            # Tol if specified
                            tol = 0.02 if m.group(1) == "A" else 0.1
                            rows.append({
                                "feature_label": f"{label} (X)",
                                "parameter": f"Hole {label} - X Coordinate",
                                "category": "COORDINATE_FEATURE",
                                "nominal": x_val,
                                "upper_tol": tol,
                                "lower_tol": -tol,
                                "lsl": round(x_val - tol, 4),
                                "usl": round(x_val + tol, 4),
                                "unit": "mm",
                                "raw_text": f"{label} X={x_val}mm",
                                "remarks": f"Callout: {callout}" if callout else "Coordinate table",
                                "source_pdf": pdf_path.name,
                                "page": pno + 1,
                            })
                            rows.append({
                                "feature_label": f"{label} (Y)",
                                "parameter": f"Hole {label} - Y Coordinate",
                                "category": "COORDINATE_FEATURE",
                                "nominal": y_val,
                                "upper_tol": tol,
                                "lower_tol": -tol,
                                "lsl": round(y_val - tol, 4),
                                "usl": round(y_val + tol, 4),
                                "unit": "mm",
                                "raw_text": f"{label} Y={y_val}mm",
                                "remarks": f"Callout: {callout}" if callout else "Coordinate table",
                                "source_pdf": pdf_path.name,
                                "page": pno + 1,
                            })

                # Case B: Multi-column Hole Tables without 'mm' (e.g., P26G2A Page 2)
                if not rows and any("HOLE TABLE" in l.upper() for l in lines):
                    for i, l in enumerate(lines):
                        m = re.match(r"^([A-I])\.(\d+)$", l)
                        if m:
                            label = f"{m.group(1)}.{m.group(2)}"
                            block = lines[i + 1: i + 8]
                            nums = []
                            feature = ""
                            for item in block:
                                if re.match(r"^-?\d+(?:\.\d+)?$", item):
                                    nums.append(float(item))
                                elif re.search(r"(?:THRU|DEEP|M\d+|Ø|O\s*\d)", item, re.I):
                                    feature = item
                                if len(nums) >= 2 and feature:
                                    break
                            if len(nums) >= 2:
                                tol = 0.02 if m.group(1) in ["F", "H"] else 0.1
                                rows.append({
                                    "feature_label": f"{label} (X)",
                                    "parameter": f"Hole {label} - X Coordinate",
                                    "category": "COORDINATE_FEATURE",
                                    "nominal": nums[0],
                                    "upper_tol": tol,
                                    "lower_tol": -tol,
                                    "lsl": round(nums[0] - tol, 4),
                                    "usl": round(nums[0] + tol, 4),
                                    "unit": "mm",
                                    "raw_text": f"{label} X={nums[0]}",
                                    "remarks": f"Feature: {feature}",
                                    "source_pdf": pdf_path.name,
                                    "page": pno + 1,
                                })
                                rows.append({
                                    "feature_label": f"{label} (Y)",
                                    "parameter": f"Hole {label} - Y Coordinate",
                                    "category": "COORDINATE_FEATURE",
                                    "nominal": nums[1],
                                    "upper_tol": tol,
                                    "lower_tol": -tol,
                                    "lsl": round(nums[1] - tol, 4),
                                    "usl": round(nums[1] + tol, 4),
                                    "unit": "mm",
                                    "raw_text": f"{label} Y={nums[1]}",
                                    "remarks": f"Feature: {feature}",
                                    "source_pdf": pdf_path.name,
                                    "page": pno + 1,
                                })

        return rows

    def extract_features(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts all inspectable engineering features from the drawing:
        - Hole Callouts & Diameters
        - Thread Callouts
        - Toleranced Dimensions
        - Standard Linear Dimensions (with IS 2102-m tolerance)
        - Chamfers, Radii, GD&T, Surface Finish
        """
        features = []
        seen_texts = set()

        with fitz.open(pdf_path) as doc:
            for pno, page in enumerate(doc):
                lines = [l.strip() for l in page.get_text().split("\n") if l.strip()]

                idx = 0
                while idx < len(lines):
                    line = lines[idx]
                    norm = self.normalize_symbols(line)

                    # Skip title block border general tolerance chart noise
                    if line in self.BORDER_TOLERANCES:
                        idx += 1
                        continue

                    # Skip standard drawing border coordinates, scale, and company stamps
                    if line in self.GRID_BOILERPLATE or line.startswith("\\\\parienggnew"):
                        idx += 1
                        continue

                    # Skip drawing general notes (manufacturing instructions)
                    if re.match(r"^\d+\.\s*(?:DEBURRING|HEAT\s*TREATMENT|SURFACE\s*TREATMENT|UNMARKED|IF\s*THE\s*DIMENSIONS|USE\s*\d+%|REFER|PAINTED|WELDING|NON-)", line, re.I):
                        idx += 1
                        continue

                    # ----------------------------------------------------
                    # 1. THREAD CALLOUTS (e.g., M5 - 6H ↧ 10, M4 - 6H THRU)
                    # ----------------------------------------------------
                    if re.search(r"\bM\d+(?:\s*[xX]\s*\d+(?:\.\d+)?)?\s*[- ]?\s*\d*H\b", line, re.I) or re.search(r"\bM\d+\s+THRU\b", line, re.I):
                        full_callout = norm
                        # Check if previous or next line was a quantity or drill hole
                        if idx > 0 and re.match(r"^\d+\s*[xX]\s*(?:Ø|O)?\s*\d+", lines[idx - 1], re.I):
                            full_callout = f"{self.normalize_symbols(lines[idx - 1])} / {norm}"

                        # Extract thread size
                        tm = re.search(r"\bM(\d+(?:\.\d+)?)", line, re.I)
                        nom = float(tm.group(1)) if tm else 0.0

                        features.append({
                            "parameter": f"Thread Feature {norm}",
                            "category": "THREAD_CALLOUT",
                            "nominal": nom,
                            "upper_tol": 0.05,
                            "lower_tol": -0.05,
                            "lsl": nom,
                            "usl": nom,
                            "unit": "Metric (6H)",
                            "raw_text": full_callout,
                            "remarks": "Check with Thread Plug Gauge (6H Go/No-Go)",
                            "source_pdf": pdf_path.name,
                            "page": pno + 1,
                        })
                        seen_texts.add(line)
                        idx += 1
                        continue

                    # ----------------------------------------------------
                    # 2. HOLE CALLOUTS & DIAMETERS (e.g. 4X Ø3.4 THRU, 2x Ø4.2 ↧12.4)
                    # ----------------------------------------------------
                    if re.search(r"(?:\b\d*\s*[xX]\s*(?:Ø|O)\s*\d+|(?:Ø|⌀)\s*\d+|\b\d+(?:\.\d+)?\s*(?:THRU|DEEP)\b)", line, re.I):
                        # Avoid duplicating if already matched in thread
                        if line not in seen_texts:
                            dia_match = re.search(r"(?:Ø|O)\s*(\d+(?:\.\d+)?)", line, re.I)
                            nom = float(dia_match.group(1)) if dia_match else 0.0
                            up_tol, lo_tol = (0.03, 0.01) if "H7" in line or "+0.03" in line else self.get_general_tolerance(nom)

                            features.append({
                                "parameter": f"Hole Callout {norm}",
                                "category": "HOLE_CALLOUT",
                                "nominal": nom,
                                "upper_tol": up_tol,
                                "lower_tol": lo_tol,
                                "lsl": round(nom + lo_tol, 4),
                                "usl": round(nom + up_tol, 4),
                                "unit": "mm",
                                "raw_text": norm,
                                "remarks": "Verify hole diameter and depth",
                                "source_pdf": pdf_path.name,
                                "page": pno + 1,
                            })
                            seen_texts.add(line)
                        idx += 1
                        continue

                    # ----------------------------------------------------
                    # 3. ASYMMETRIC LIMIT TOLERANCES (e.g., 250 +0.03 / +0.01 or 25 -0.01 / -0.03)
                    # ----------------------------------------------------
                    asym_m = re.match(r"^(\d+(?:\.\d+)?)\s*([+-]\d+\.\d+)$", line)
                    if asym_m and idx + 1 < len(lines):
                        next_line = lines[idx + 1].strip()
                        second_tol_m = re.match(r"^([+-]\d+\.\d+)$", next_line)
                        if second_tol_m:
                            nom = float(asym_m.group(1))
                            t1 = float(asym_m.group(2))
                            t2 = float(second_tol_m.group(1))
                            up_tol = max(t1, t2)
                            lo_tol = min(t1, t2)
                            features.append({
                                "parameter": f"Toleranced Dimension {nom} (+{up_tol}/{lo_tol})",
                                "category": "TOLERANCED_DIMENSION",
                                "nominal": nom,
                                "upper_tol": up_tol,
                                "lower_tol": lo_tol,
                                "lsl": round(nom + lo_tol, 4),
                                "usl": round(nom + up_tol, 4),
                                "unit": "mm",
                                "raw_text": f"{nom} {t1}/{t2}",
                                "remarks": "Precision fit dimension",
                                "source_pdf": pdf_path.name,
                                "page": pno + 1,
                            })
                            seen_texts.add(line)
                            idx += 2
                            continue

                    # ----------------------------------------------------
                    # 4. SYMMETRIC TOLERANCED DIMENSIONS (e.g., 16±0.02, 1.5±0.01, 8±0.5)
                    # ----------------------------------------------------
                    sym_m = re.search(r"^(\d+(?:\.\d+)?)\s*±\s*(\d+(?:\.\d+)?)(?:\s*\(.*?\))?$", line)
                    if sym_m:
                        nom = float(sym_m.group(1))
                        tol = float(sym_m.group(2))
                        features.append({
                            "parameter": f"Precision Dimension {nom} ± {tol}",
                            "category": "TOLERANCED_DIMENSION",
                            "nominal": nom,
                            "upper_tol": tol,
                            "lower_tol": -tol,
                            "lsl": round(nom - tol, 4),
                            "usl": round(nom + tol, 4),
                            "unit": "mm",
                            "raw_text": norm,
                            "remarks": "Critical inspection dimension",
                            "source_pdf": pdf_path.name,
                            "page": pno + 1,
                        })
                        seen_texts.add(line)
                        idx += 1
                        continue

                    # ----------------------------------------------------
                    # 5. CHAMFERS (e.g., 0.5 x 45°, 1 x 45°, 4-C1, 4-C)
                    # ----------------------------------------------------
                    if re.search(r"\b(?:\d+(?:\.\d+)?\s*[xX]\s*45[°\s]*|\d+\s*-\s*C\d*)\b", line, re.I):
                        features.append({
                            "parameter": f"Chamfer {norm}",
                            "category": "CHAMFER",
                            "nominal": 1.0,
                            "upper_tol": 0.2,
                            "lower_tol": -0.2,
                            "lsl": 0.8,
                            "usl": 1.2,
                            "unit": "mm x deg",
                            "raw_text": norm,
                            "remarks": "Verify edge deburring & chamfer angle",
                            "source_pdf": pdf_path.name,
                            "page": pno + 1,
                        })
                        seen_texts.add(line)
                        idx += 1
                        continue

                    # ----------------------------------------------------
                    # 6. RADII (e.g., R 0.5, R 2 TYP, R 3, R 5, R 10)
                    # ----------------------------------------------------
                    if re.match(r"^(?:\d+\s*[xX]\s*)?R\s*(\d+(?:\.\d+)?)(?:\s*TYP\.?)?$", line, re.I):
                        rad_m = re.search(r"R\s*(\d+(?:\.\d+)?)", line, re.I)
                        nom = float(rad_m.group(1)) if rad_m else 1.0
                        features.append({
                            "parameter": f"Fillet Radius {norm}",
                            "category": "RADIUS",
                            "nominal": nom,
                            "upper_tol": 0.2,
                            "lower_tol": -0.2,
                            "lsl": round(nom - 0.2, 4),
                            "usl": round(nom + 0.2, 4),
                            "unit": "mm",
                            "raw_text": norm,
                            "remarks": "Inspect with Radius Gauge Set",
                            "source_pdf": pdf_path.name,
                            "page": pno + 1,
                        })
                        seen_texts.add(line)
                        idx += 1
                        continue

                    # ----------------------------------------------------
                    # 7. GD&T (e.g. ⌖ 0.05 A, // 0.03, // 0.06 A)
                    # ----------------------------------------------------
                    if re.search(r"\b(?:[nir]\s*0\.\d+\s*[A-Z]?|⌖\s*0\.\d+)\b", line):
                        features.append({
                            "parameter": f"GD&T Specification {norm}",
                            "category": "GEOMETRIC_TOLERANCE",
                            "nominal": 0.0,
                            "upper_tol": 0.05,
                            "lower_tol": 0.0,
                            "lsl": 0.0,
                            "usl": 0.05,
                            "unit": "mm",
                            "raw_text": norm,
                            "remarks": "Geometric feature control (Position / Runout / Parallelism)",
                            "source_pdf": pdf_path.name,
                            "page": pno + 1,
                        })
                        seen_texts.add(line)
                        idx += 1
                        continue

                    # ----------------------------------------------------
                    # 8. SURFACE FINISH (e.g., 3.2, Ra 3.2)
                    # ----------------------------------------------------
                    if line in ["3.2", "1.6", "0.8", "6.3"] and any("ROUGHNESS" in prev.upper() for prev in lines[max(0, idx-5):idx]):
                        features.append({
                            "parameter": f"Surface Roughness Ra {line}",
                            "category": "SURFACE_FINISH",
                            "nominal": float(line),
                            "upper_tol": 0.5,
                            "lower_tol": -0.5,
                            "lsl": 0.0,
                            "usl": float(line),
                            "unit": "µm",
                            "raw_text": f"Ra {line} µm",
                            "remarks": "Inspect with Portable Surface Roughness Tester",
                            "source_pdf": pdf_path.name,
                            "page": pno + 1,
                        })
                        seen_texts.add(line)
                        idx += 1
                        continue

                    # ----------------------------------------------------
                    # 9. GENERAL LINEAR DIMENSIONS (e.g., 18, 26, 204.5, 360, 510)
                    # ----------------------------------------------------
                    # Pure positive numbers representing linear dimensions
                    num_m = re.match(r"^(\d+(?:\.\d+)?)$", line)
                    if num_m:
                        val = float(num_m.group(1))
                        # Mechanical parts in these drawings are <= 2000 mm. Filter out ERP IDs, years, etc.
                        if 2.0 < val <= 2000.0 and int(val) not in [2024, 2025, 2026, 1200]:
                            up_tol, lo_tol = self.get_general_tolerance(val)
                            features.append({
                                "parameter": f"Linear Dimension {val} mm",
                                "category": "LINEAR_DIMENSION",
                                "nominal": val,
                                "upper_tol": up_tol,
                                "lower_tol": lo_tol,
                                "lsl": round(val + lo_tol, 4),
                                "usl": round(val + up_tol, 4),
                                "unit": "mm",
                                "raw_text": f"{val} mm",
                                "remarks": "Tolerance as per IS 2102-m / ISO 2768-m",
                                "source_pdf": pdf_path.name,
                                "page": pno + 1,
                            })
                            seen_texts.add(line)

                    idx += 1

        # Deduplicate features by (parameter, nominal)
        unique_features = []
        seen_keys = set()
        for f in features:
            k = (f["category"], f["nominal"], f["raw_text"])
            if k not in seen_keys:
                seen_keys.add(k)
                f["inspection_tool"] = self.suggest_tool(f["category"], f["nominal"], f["upper_tol"] - f["lower_tol"])
                unique_features.append(f)

        return unique_features

    def extract_all(self, pdf_path: Path) -> Dict[str, Any]:
        """Extracts metadata, coordinates, and features for a given drawing."""
        metadata = self.extract_metadata(pdf_path)
        coord_rows = self.extract_coordinate_table(pdf_path)
        feat_rows = self.extract_features(pdf_path)

        # Assign inspection tools for coordinates
        for c in coord_rows:
            c["inspection_tool"] = self.suggest_tool(c["category"], c["nominal"], c["upper_tol"] - c["lower_tol"])

        return {
            "metadata": metadata,
            "coordinates": coord_rows,
            "features": feat_rows,
            "total_items": len(coord_rows) + len(feat_rows),
        }
