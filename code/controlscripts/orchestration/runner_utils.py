import asyncio
import random
import shlex
import string


# Runner Utils contains functions to facilitate the command execution on the
# local or a remote host. Command & Control happens over SSH.

# A *Runner* denotes the target. So local or Remote-Via-SSH

# *SyncRunner* runs something on the runner and blocks execution
# *BGRunner* runs something on the runner and *not* blocks execution.

class LocalRunner:
    def __init__(self):
        pass
    
    def name(self):
        return "local"

    def start(self, process):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_start(process))
    
    def copyFromMeToYou(self, myfile, yourfile, remove=False):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_copyFromMeToYou(myfile, yourfile, remove=False))
    
    async def async_start(self, process):
        return await process.async_start(self)
    
    async def run(self, cmd, use_pipes=True):
        if use_pipes:
            return self, await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        else:
            return self, await asyncio.create_subprocess_shell(cmd)
    
    async def communicate(self, p):
        m, p = p
        assert(m == self)
        stdout, stderr = await p.communicate()
        ret = p.returncode
        return ret, stdout.decode(), stderr.decode()
    
    async def async_copyFromMeToYou(self, myfile, yourfile, remove):
        cmd = "cp {} {}".format(myfile, yourfile)
        p = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await p.communicate()
        ret = p.returncode
        if ret != 0:
            raise ChildProcessError("Error copying")
        if remove:
            cmd = "rm {}".format(myfile)
            p = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await p.communicate()
            ret = p.returncode
            if ret != 0:
                raise ChildProcessError("Error removing")

class SSHRunner:
    def __init__(self, hostname, username):
        self.hostname = hostname
        self.username = username
    
    def name(self):
        return "%s@%s" % (self.username, self.hostname)

    def start(self, process):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_start(process))
    
    def copyFromMeToYou(self, myfile, yourfile, remove=False):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_copyFromMeToYou(myfile, yourfile, remove))
    
    async def async_start(self, process):
        return await process.async_start(self)

    async def run(self, scmd, use_pipes=True):
        cmd = "ssh -t {}@{} {}".format(self.username, self.hostname, shlex.quote("set -m; bash -l -i -c '" + scmd + "'"))
        if use_pipes:
            return self, await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        else:
            return self, await asyncio.create_subprocess_shell(cmd)
    
    async def communicate(self, p):
        m, p = p
        assert(m == self)
        stdout, stderr = await p.communicate()
        ret = p.returncode
        return ret, stdout.decode(), stderr.decode()
    
    async def async_copyFromMeToYou(self, myfile, yourfile, remove=False):
        cmd = "scp {}@{}:{} {}".format(self.username, self.hostname, myfile, yourfile)
        p = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await p.communicate()
        ret = p.returncode
        if ret != 0:
            raise ChildProcessError("Error copying (return {}) {} {}".format(ret, stdout, stderr))
        if remove:
            cmd = "ssh -t {}@{} sudo rm {}".format(self.username, self.hostname, myfile)
            p = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await p.communicate()
            ret = p.returncode
            if ret != 0:
                raise ChildProcessError("Error removing (return {}) {} {}".format(ret, stdout, stderr))

class SyncProc:
    def __init__(self, command, wanted_ret=[0], parser=None, sudo=False):
        self.command = command
        self.wanted_ret = wanted_ret
        self.returncode = None
        self.stdout = None
        self.stderr = None
        self.parser = parser
        self.sudo = sudo
    
    def start(self, machine):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_start(machine))
    
    async def async_start(self, machine):
        p = await machine.run(self.command, use_pipes=True)
        ret, stdout, stderr = await machine.communicate(p)

        self.returncode = ret
        self.stdout = stdout
        self.stderr = stderr
        
        if self.wanted_ret is not None and self.returncode not in self.wanted_ret:
            if self.returncode == 130:
                raise KeyboardInterrupt
            else:
                raise ChildProcessError("Error executing {} on {} (return {}) {} {}".format(self.command, machine.name(), self.returncode, self.stdout, self.stderr))
        if self.parser is None:
            return self.returncode, self.stdout, self.stderr
        else:
            return self.parser(self.returncode, self.stdout, self.stderr)

def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

class BGProc:
    def __init__(self, command, sudo=False, log=False, logfile=None):
        self.command = command
        self.returncode = None
        self.stdout = None
        self.stderr = None
        self.m = None
        self.pid = None
        self.sudo = sudo
        self.log = log
        self.logfile = logfile
    
    def start(self, machine):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_start(machine))
    
    def is_running(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_is_running())
    
    def stop(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_stop())
    
    async def async_start(self, machine):
        self.m = machine
        if self.logfile is None:
            if self.log:
                self.logfile = "/tmp/" + randomword(32)
            else:
                self.logfile = "/dev/null"
        command = "nohup " + self.command + " > %s 2>&1 & echo $!" % self.logfile
        p = await machine.run(command, use_pipes=True)
        ret, stdout, stderr = await machine.communicate(p)
        if ret != 0:
            raise ChildProcessError("Error executing {} on {} (return {}) {} {}".format(command, self.m.name(), ret, stdout, stderr))
        pid = stdout.split("\n")[-2]
        self.pid = int(pid)
        return self
    
    async def async_is_running(self):
        assert(self.m is not None)
        assert(self.pid is not None)
        command = "ps -p {}".format(self.pid)
        p = await self.m.run(command, use_pipes=True)
        ret, stdout, stderr = await self.m.communicate(p)
        return ret == 0
    
    async def async_stop(self):
        assert(self.m is not None)
        assert(self.pid is not None)
        if self.sudo:
            command = "sudo kill $(ps --ppid {} -o pid=)".format(self.pid)
        else:
            command = "kill {}".format(self.pid)
        p = await self.m.run(command, use_pipes=True)
        ret, stdout, stderr = await self.m.communicate(p)
        if ret != 0:
            raise ChildProcessError("Error killing {} on {} (return {}) {} {}".format(self.command, self.m.name(), ret, stdout, stderr))
        return ret == 0


