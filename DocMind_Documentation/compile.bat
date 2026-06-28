@echo off
REM ─── Compile main.tex with XeLaTeX (no Perl / latexmk required) ─────────────
REM XeLaTeX is run 3 times so the Table of Contents, List of Figures, and
REM List of Tables fully populate (each needs the previous pass's .toc/.lof/.lot).
cd /d "%~dp0"

echo ===== Pass 1 of 3 =====
xelatex -interaction=nonstopmode -synctex=1 main.tex
echo ===== Pass 2 of 3 =====
xelatex -interaction=nonstopmode -synctex=1 main.tex
echo ===== Pass 3 of 3 =====
xelatex -interaction=nonstopmode -synctex=1 main.tex

echo.
echo ===== Cleaning up temporary files =====
del /q main.aux main.lof main.log main.lot main.out main.toc main.synctex.gz 2>nul

echo.
echo ===== Done. Output: main.pdf =====
pause
