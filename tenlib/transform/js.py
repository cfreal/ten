from tenlib.transform.generic import wrap_join_format


from_char_code = wrap_join_format("String.fromCharCode({})", "{}", ",")
"""`'ABCDEF'` -> `String.fromCharCode(65,66,67,68,69,70)`"""
