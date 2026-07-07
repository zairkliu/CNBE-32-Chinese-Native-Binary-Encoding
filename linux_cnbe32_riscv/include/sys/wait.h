#ifndef _SYS_WAIT_H
#define _SYS_WAIT_H

#define WNOHANG     0x00000001
#define WUNTRACED   0x00000002

#define WIFEXITED(status)   (((status) & 0xFF) == 0)
#define WIFSIGNALED(status) (((status) & 0xFF) != 0 && ((status) & 0xFF) != 0xFF)
#define WIFSTOPPED(status)  (((status) & 0xFF) == 0xFF)
#define WEXITSTATUS(status) (((status) >> 8) & 0xFF)
#define WTERMSIG(status)    ((status) & 0x7F)
#define WSTOPSIG(status)    (((status) >> 8) & 0xFF)

#define _LOW(v)     ((unsigned short)(v))
#define _HIGH(v)    ((unsigned short)(((unsigned)(v)) >> 16))

typedef int pid_t;

#endif
