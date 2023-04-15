from tenlib.transform.generic import wrap_join_format


dot_chr = wrap_join_format("{}", "chr({})", ".", "trim(chr(32))")
"""`'ABC'` -> `'chr(65).chr(66).chr(67)'`"""
