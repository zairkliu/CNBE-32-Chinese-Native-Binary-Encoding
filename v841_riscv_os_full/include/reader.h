#ifndef READER_H
#define READER_H

void reader_init(void);
void reader_enter(void);
void reader_display(void);
void reader_stats(void);
void reader_load_daodejing(void);
void reader_save(const char *fname);
void reader_load(const char *fname);

#endif
