from tornado.process import Subprocess
from tornado.iostream import PipeIOStream


class AASubprocess(Subprocess):
    """
    Extension to tornado.process.Subprocess to support
    - process timeout
    - pass stdin bytes
    - real-time stdout data chunk callback
    - real-time stderr data chunk callback
    - process end callback
    """
    def __init__(
                self,
                command,
                timeout=-1,
                stdout_chunk_callback=None,
                stderr_chunk_callback=None,
                exit_process_callback=None,
                stdin_bytes=None,
                io_loop=None,
                kill_on_timeout=False
                ):
        """
        Initializes the subprocess with callbacks and timeout.

        :param command: command like ['java', '-jar', 'test.jar']
        :param timeout: timeout for subprocess to complete, if negative or zero then no timeout
        :param stdout_chunk_callback: callback(bytes_data_chuck_from_stdout)
        :param stderr_chunk_callback: callback(bytes_data_chuck_from_stderr)
        :param exit_process_callback: callback(exit_code, was_expired_by_timeout)
        :param stdin_bytes: bytes data to send to stdin
        :param io_loop: tornado io loop on None for current
        :param kill_on_timeout: kill(-9) or terminate(-15)?
        """
        self.aa_exit_process_callback = exit_process_callback
        self.aa_kill_on_timeout = kill_on_timeout
        stdin = Subprocess.STREAM if stdin_bytes else None
        stdout = Subprocess.STREAM if stdout_chunk_callback else None
        stderr = Subprocess.STREAM if stderr_chunk_callback else None

        Subprocess.__init__(self, command, stdin=stdin, stdout=stdout, stderr=stderr, io_loop=io_loop)

        self.aa_process_expired = False
        self.aa_terminate_timeout = self.io_loop.call_later(timeout, self.aa_timeout_callback) if timeout > 0 else None

        self.set_exit_callback(self.aa_exit_callback)

        if stdin:
            self.stdin.write(stdin_bytes)
            self.stdin.close()

        if stdout:
            output_stream = PipeIOStream(self.stdout.fileno())

            def on_stdout_chunk(data):
                stdout_chunk_callback(data)
                if not output_stream.closed():
                    output_stream.read_bytes(102400, on_stdout_chunk, None, True)

            output_stream.read_bytes(102400, on_stdout_chunk, None, True)

        if stderr:
            stderr_stream = PipeIOStream(self.stderr.fileno())

            def on_stderr_chunk(data):
                stderr_chunk_callback(data)
                if not stderr_stream.closed():
                    stderr_stream.read_bytes(102400, on_stderr_chunk, None, True)

            stderr_stream.read_bytes(102400, on_stderr_chunk, None, True)

    def aa_timeout_callback(self):
        if self.aa_kill_on_timeout:
            self.proc.kill()
        else:
            self.proc.terminate()
        self.aa_process_expired = True

    def aa_exit_callback(self, status):
        if self.aa_terminate_timeout:
            self.io_loop.remove_timeout(self.aa_terminate_timeout)
        # need to post this call to make sure it is processed AFTER all outputs
        if self.aa_exit_process_callback:
            self.io_loop.add_callback(self.aa_exit_process_callback, status, self.aa_process_expired)


def main():
    from tornado.ioloop import IOLoop
    from functools import partial

    loop = IOLoop.instance()

    def on_data(source, data):
        print('%s : %s' % (source, data.decode().strip()))

    def test1():
        cmd = ['/bin/bash', '-c', 'echo -n Hello1']
        print('test1:', cmd)
        AASubprocess(cmd, 4, partial(on_data, 'out1'), None, None)

    def test2():
        cmd = ['/bin/bash', '-c', 'cp 98483 53983']
        print('test2:', cmd)
        def on_done(exit_code, expired):
            print('done2: %d, expired?: %s' % (exit_code, expired))
        AASubprocess(cmd, 4, partial(on_data, 'out2'), partial(on_data, 'err2'), on_done)

    def test3():
        cmd = ['/bin/bash', '-c', 'sleep 3']
        print('test3:', cmd)
        def on_done(exit_code, expired):
            print('done3: %d, expired?: %s' % (exit_code, expired))
        AASubprocess(cmd, 2, None, None, on_done)

    def test4():
        cmd = ['/bin/bash', '-c', 'cat|wc']
        print('test4:', cmd)
        AASubprocess(cmd, 4, partial(on_data, 'out4'), None,  None, b'test')

    test1()
    test2()
    test3()
    test4()

    loop.call_later(4, loop.stop)
    loop.start()

if __name__ == '__main__':
    main()
