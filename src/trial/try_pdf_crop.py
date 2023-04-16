"""
PDF Cropの試験
-> OK!!!
- GhostScriptいるかも？？
"""
from pdfCropMargins import crop

crop(["-p", "0", "-s",
      "/Users/hirots-m/Documents/PyCharmProjects/src/src/test/fig_src/test_pdf.pdf",
      "-o",
      "/Users/hirots-m/Documents/PyCharmProjects/src/src/test/fig_src/out_pdf.pdf"
      ])

# crop(["-p", "20", "-u", "-s",
#       "/Users/hirots-m/Documents/PyCharmProjects/src/src/test/fig_src/test_pdf.pdf",
#       "-o",
#       "/Users/hirots-m/Documents/PyCharmProjects/src/src/test/fig_src/out_pdf.pdf"
#       ])
# crop(["-p", "0", "-gui",
#       "/Users/hirots-m/Documents/PyCharmProjects/src/src/test/fig_src/test_pdf.pdf"])
