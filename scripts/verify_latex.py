"""Check freshly compiled documents, citations, overflow and author metadata."""
import re
from pypdf import PdfReader
from context import ROOT,PAPER,report

names=('Ali Sayghe','Husam A. Bakhsh','Olugbenga Moses Anubi')
result={};citations=[]
for target in ('main','supplement','title_page','cover_letter_draft','highlights_draft'):
 log=(PAPER/(target+'.log')).read_text()
 warnings=[line for line in log.splitlines() if any(token in line for token in ('Overfull','Underfull','LaTeX Warning','Package natbib Warning','Package hyperref Warning'))]
 assert not warnings,(target,warnings)
 pdf=PdfReader(PAPER/(target+'.pdf'))
 author=pdf.metadata.author
 assert all(name in author for name in names) and [author.index(name) for name in names]==sorted(author.index(name) for name in names)
 assert 'sayghea@rcjy.edu.sa' in pdf.metadata.subject
 assert 'Yanbu Industrial College' in pdf.metadata.subject and 'FAMU-FSU College of Engineering' in pdf.metadata.subject and 'Center for Advanced Power Systems' in pdf.metadata.subject
 if target in ('main','supplement','title_page'):
  original=PdfReader(ROOT/'manuscript'/(target+'.pdf'))
  assert len(original.pages)==len(pdf.pages)
  assert [p.extract_text() for p in original.pages]==[p.extract_text() for p in pdf.pages],target
 if target in ('main','supplement'):
  matches=re.findall(r'\\bibcite\{([^}]+)\}\{\{(\d+)\}',(PAPER/(target+'.aux')).read_text())
  assert len(matches)==17;citations.append(matches)
 result[target]={'pages':len(pdf.pages),'warnings':warnings,'author_metadata':'PASS'}
assert citations[0]==citations[1]
report('LATEX_VERIFICATION.json',{'status':'PASS','documents':result,'numbered_references':17,'citation_numbering_matches':True,'full_page_raster_inspection':False,'limitation':'Compiler, extracted-text and metadata checks were completed; full rendered-page inspection was not available in this environment.'})
print('LaTeX builds, 17 references and author consistency: PASS')
