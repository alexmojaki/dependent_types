def needs_parentheses(source):
    def code(s):
        return compile(s.format(source), '<variable>', 'eval').co_code

    try:
        without_parens = code('{}.x')
    except SyntaxError:
        return True
    else:
        return without_parens != code('({}).x')


def with_needed_parens(source):
    if needs_parentheses(source):
        return '({})'.format(source)
    else:
        return source
