"""Coordinator-only: reflow a prepared copy with Hangeul and export review PDF."""
import hashlib
import json
import sys
from pathlib import Path
import win32com.client

src, dst, pdf = (Path(x).resolve() for x in sys.argv[1:4])
assert src != dst and not dst.exists() and not pdf.exists()
before = hashlib.sha256(src.read_bytes()).hexdigest()
hwp = win32com.client.DispatchEx('HWPFrame.HwpObject')
result = {}
try:
    hwp.XHwpWindows.Item(0).Visible = False
    result['registered'] = bool(hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule'))
    result['open'] = bool(hwp.Open(str(src), 'HWPX', 'forceopen:true'))
    assert result['open'], 'Hangeul Open=False'
    result['pages'] = int(hwp.PageCount)
    result['save_hwpx'] = bool(hwp.SaveAs(str(dst), 'HWPX', ''))
    assert result['save_hwpx'] and dst.exists(), 'HWPX SaveAs failed'
    result['save_pdf'] = bool(hwp.SaveAs(str(pdf), 'PDF', ''))
    assert result['save_pdf'] and pdf.exists(), 'PDF SaveAs failed'
finally:
    hwp.Clear(1)
    hwp.Quit()
result['source_unchanged'] = before == hashlib.sha256(src.read_bytes()).hexdigest()
assert result['source_unchanged']
print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
