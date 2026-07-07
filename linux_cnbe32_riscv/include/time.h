#ifndef _TIME_H
#define _TIME_H

struct tm {
	int tm_sec;
	int tm_min;
	int tm_hour;
	int tm_mday;
	int tm_mon;
	int tm_year;
	int tm_wday;
	int tm_yday;
	int tm_isdst;
};

struct utimbuf {
	long actime;
	long modtime;
};

typedef long time_t;

extern long timezone;

#endif
