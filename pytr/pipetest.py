import win32pipe, win32file

def pipe_test(pipe):
    with open(pipe,'wt') as f:
        if not f.closed:
            f.write('+33123124124\n1231')