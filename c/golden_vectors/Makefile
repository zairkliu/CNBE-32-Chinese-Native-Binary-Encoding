CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -pedantic

BIN := cnbe32_golden_test
SRC := cnbe32_golden_test.c

.PHONY: all test clean

all: $(BIN)

$(BIN): $(SRC)
	$(CC) $(CFLAGS) -o $(BIN) $(SRC)

test: $(BIN)
	./$(BIN)

clean:
	rm -f $(BIN)
# integrity check: 1783623667
