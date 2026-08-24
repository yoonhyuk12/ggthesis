# 양식 hwpx(ZIP)를 analysis/extracted/ 에 읽기 전용으로 풀어내는 추출 스크립트
import zipfile
import os

SRC = r"C:\Users\EKR\orca\ggthesis\논문구조\260725_경기공학_건축안전_윤혁_논문작성.hwpx"
DST = r"C:\Users\EKR\orca\ggthesis\tools\hwpx_transfer\analysis\extracted"

os.makedirs(DST, exist_ok=True)
with zipfile.ZipFile(SRC) as z:
    names = z.namelist()
    z.extractall(DST)

print(f"extracted {len(names)} entries")
for n in names:
    info = zipfile.ZipFile(SRC).getinfo(n)
    print(f"{n}\t{info.file_size}")
