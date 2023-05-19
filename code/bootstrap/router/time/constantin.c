#include <linux/module.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/timekeeping.h>
#include <linux/moduleparam.h>
#include <linux/proc_fs.h>
#include <linux/uaccess.h>

#define BUFSIZE 100

static ssize_t proc_file_written(struct file *file, const char __user *ubuf, size_t count, loff_t *ppos);
static ssize_t proc_file_read(struct file *file, char __user *ubuf, size_t count, loff_t *ppos);

static struct proc_dir_entry *ent;

static struct file_operations file_ops = {.owner = THIS_MODULE, .read = proc_file_read, .write = proc_file_written};

static int __init init(void)
{
  s64 o = ktime_mono_to_any(0, TK_OFFS_REAL);
  printk(KERN_INFO "constantin mono2real loaded; offset %lld\n", o);
  ent = proc_create("constantin", 0, NULL, &file_ops);
  return 0;
}

static void __exit cleanup(void)
{
  printk(KERN_INFO "constantin mono2real unloaded;\n");
  proc_remove(ent);
}

static ssize_t proc_file_written(struct file *file, const char __user *ubuf, size_t count, loff_t *ppos)
{
  return -1;
}

static ssize_t proc_file_read(struct file *file, char __user *ubuf, size_t count, loff_t *ppos)
{
  char buf[BUFSIZE];
  s64 o;
  int len = 0;

  if (*ppos > 0 || count < BUFSIZE)
    return 0;

  o = ktime_mono_to_any(0, TK_OFFS_REAL);
  len += sprintf(buf, "%lld\n", o);

  if (copy_to_user(ubuf, buf, len))
    return -EFAULT;

  *ppos = len;
  return len;
}

module_init(init);
module_exit(cleanup);

MODULE_AUTHOR("Constantin Sander");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("get mono to time offset");