#include <stddef.h>
#include <string.h>

#include "espeak-ng/speak_lib.h"

#define OUTPUT_CAPACITY 65536

static char output[OUTPUT_CAPACITY];
static int initialized = 0;

int main(void) {
	return 0;
}
const char *difonos_phonemize(const char *text) {
	const void *cursor;
	const void *previous;
	const char *clause;
	int terminator = 0;
	size_t used = 0;

	if (!text)
		return "";
	if (!initialized) {
		if (espeak_Initialize(AUDIO_OUTPUT_SYNCHRONOUS, 0, "/", espeakINITIALIZE_DONT_EXIT) < 0)
			return "";
		initialized = 1;
	}
	if (espeak_SetVoiceByName("en-us") != EE_OK)
		return "";

	output[0] = '\0';
	cursor = text;
	while (cursor && *(const char *)cursor && used < OUTPUT_CAPACITY - 1) {
		previous = cursor;
		clause = espeak_TextToPhonemesWithTerminator(&cursor, espeakCHARS_UTF8,
											   espeakPHONEMES_IPA | ('|' << 8), &terminator);
		if (clause && *clause) {
			size_t length = strlen(clause);
			if (length > OUTPUT_CAPACITY - used - 1)
				length = OUTPUT_CAPACITY - used - 1;
			memcpy(output + used, clause, length);
			used += length;
			output[used] = '\0';
		}
		if (cursor == previous)
			break;
	}
	return output;
}
