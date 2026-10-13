"""Compile the final Q4 report without regenerating its user-edited wording."""
from pathlib import Path
import argparse
import re
import shutil
import subprocess

def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-markdown', action='store_true', help='Rebuild LaTeX from the edited Markdown (requires Pandoc).')
    parser.add_argument('--report-dir', type=Path, default=here / 'report')
    args = parser.parse_args()
    report = args.report_dir.resolve()
    if args.from_markdown:
        if not shutil.which('pandoc'):
            raise SystemExit('Install Pandoc to compile from Markdown.')
        text = (report / 'Q4_Report_Editable.md').read_text(encoding='utf-8').replace('.png)', '.pdf)')
        text=text.replace('## Model and modelling choices',r'\newpage'+'\n\n'+'## Model and modelling choices')
        text=text.replace('### Detailed comparison by risk aversion',r'\needspace{10\baselineskip}'+'\n\n'+'### Detailed comparison by risk aversion')
        (report / 'Q4_Report_PDF_Source.md').write_text(re.sub(r'!\[Figure \d+\. ', '![' , text), encoding='utf-8')
        subprocess.run(['pandoc', 'Q4_Report_PDF_Source.md', '-s', '-t', 'latex', '-o', 'Q4_Complete_Report.tex', '--include-in-header', 'header.tex', '-V', 'geometry:margin=20mm', '-V', 'fontsize:10pt', '-V', 'papersize:a4', '--resource-path', '.'], cwd=report, check=True)
        tex = report / 'Q4_Complete_Report.tex'
        tex.write_text(tex.read_text(encoding='utf-8').replace(r'\begin{figure}', r'\begin{figure}[H]'), encoding='utf-8')
    if not shutil.which('pdflatex'):
        raise SystemExit('Install a LaTeX distribution containing pdflatex to build the PDF.')
    for _ in range(2):
        subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'Q4_Complete_Report.tex'], cwd=report, check=True)
    print('Compiled:', report / 'Q4_Complete_Report.pdf')

if __name__ == '__main__':
    main()
