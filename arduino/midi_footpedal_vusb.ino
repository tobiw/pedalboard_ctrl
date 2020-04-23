/*
 * Requires USBMIDI to be installed as Arduino library:
 * https://github.com/BlokasLabs/USBMIDI
 * Vendor and device IDs/strings can be changed in library code.
 * 
 * For ATmega328P with 16MHz crystal.
 * D+ on INT0/PD2/D1, D- on PD4/D4
 * 
 * Program with avrdude (fuses: -U lfuse:w:0xDF:m -U hfuse:w:0xDA:m -U efuse:w:0xFD:m)
 * 
 * Functionality:
 * Sends MIDI Control Change (CC) (10, 11, ..., 17) message for each switch.
 * Can also be configured to send PC (Program Change) (0, ..., 7) instead.
 * Each row of switches can be configured to either always send value 127 when pressed,
 * or to toggle between 0 and 127 (see DIP switch configuration below).
 * 
 * DIP switches on the PCB can be used for configuration:
 * DIP1: set bottom row to toggle (send 0->127->0 instead of always 127)
 * DIP2: set top row to toggle
 * DIP3: enable internal LED state handling (light LED when CC value is 127)
 * DIP4: enable analog input jack (for expression pedal)
 * DIP5: shift CC# by +70 (for a device that expects CC# 80, 81, etc)
 * DIP6: set bottom row to send PC
 * DIP7: ...
 * DIP8: enable MIDI message debug display
 */

#include <midi_serialization.h>
#include <usbmidi.h>
#include <TM1638.h>

// Pin definitions and connected devices
uint8_t DIP_PINS[4] = { A0, A1, A2, A3 }; // PC0 - PC3
#define PIN_EXPRESSION_INPUT A5 // PC5
TM1638 module(8, 9, 10); // data, clock and strobe

// Enums and typedefs
typedef enum {
  MIDI_MODE_CC = 0, // send CC messages
  MIDI_MODE_PC // send PC messages
} midimode_t;

typedef enum {
  MIDI_CC_SEND_ON = 0, // only send 127 when switch pressed
  MIDI_CC_SEND_OFF_ON // send 127, then 0, then 127, etc
} switchmode_t;

// Constants
#define ENABLE_MIDI 1
const unsigned int CHANNEL = 1;
#define CC_EXP_PEDAL 9
#define MS_24H 86400000

// Internal wiring
const byte KEYMAP[8] = { 0, 1, 4, 5, 2, 6, 3, 7 };
const byte LEDMAP[8] = { 7, 5, 4, 1, 6, 3, 2, 0 };

// Global variables
char cur_display[9] = "--------\0";
unsigned char last_expression_value = 0;

// Board configuration
midimode_t midi_mode = MIDI_MODE_CC;
switchmode_t switchmode_top = MIDI_CC_SEND_ON, switchmode_bottom = MIDI_CC_SEND_ON;
bool expression_pedal_enabled = false;
bool internal_led_control = false;
bool debug_display = false;

// Helper functions
bool is_shift_cc_enabled (void) {
  //return digitalRead(DIP_PINS[5]) == LOW;
  return false;
}

void sendCC(uint8_t control, uint8_t value) {
  if (is_shift_cc_enabled())
    control += 70; // shift to 80 as first button (for MIDI expander loops)
	USBMIDI.write(0xB0 | (CHANNEL & 0xf));
	USBMIDI.write(control & 0x7f);
	USBMIDI.write(value & 0x7f);
}

void sendPC(uint8_t pc) {
  USBMIDI.write(0xC0 | (CHANNEL & 0xf));
  USBMIDI.write(pc & 0x7f);
  USBMIDI.write(0);
}

void parse_dip() {
  uint8_t dip_states[4];

  for (int i = 0; i < sizeof(DIP_PINS); i++)
  {
    dip_states[i] = digitalRead(DIP_PINS[i]);
    cur_display[i] = dip_states[i] == LOW ? '1' : '0';
  }

  // DIP 1 and 2 set bottom and top row switch modes
  switchmode_bottom = dip_states[0] == LOW ? MIDI_CC_SEND_ON : MIDI_CC_SEND_OFF_ON;
  switchmode_top = dip_states[1] == LOW ? MIDI_CC_SEND_ON : MIDI_CC_SEND_OFF_ON;

  // DIP 3 enables internal LED control (otherwise external CC input)
  internal_led_control = dip_states[2] == LOW;

  // DIP 4 sets expression input active state
  if (dip_states[3] == LOW) {
    expression_pedal_enabled = true;
    last_expression_value = analogRead(PIN_EXPRESSION_INPUT);
  }

  // DIP 5 sets MIDI PC mode (send program changes instead of control changes)
  //midi_mode = dip_states[4] == LOW ? MIDI_MODE_PC : MIDI_MODE_CC;
  
  // DIP 6 sets overall CC# offset (+70)
  // -> checked at every MIDI send call

  // DIP 7 ...

  // DIP8 enables MIDI message debug display
  debug_display = dip_states[7] == LOW;
}

void setup() {
  int i;
  
  for (i = 0; i < sizeof(DIP_PINS); i++)
  {
    pinMode(DIP_PINS[i], INPUT_PULLUP);
  }

  pinMode(PIN_EXPRESSION_INPUT, INPUT);

  delay(100);

  parse_dip();

  //pinMode(PIN_EXP_PEDAL, INPUT);
  //calibrate_analog_input(PIN_EXP_PEDAL, &expPedalMin, &expPedalMax);
  //last_exp_pedal = analogRead(PIN_EXP_PEDAL);

  // Self-test LEDs
  for (int i = 0; i < 8; i++) {
    module.setLEDs(1 << LEDMAP[i]);
    delay(200);
  }
  module.setLEDs(0);

  // Self-test segment display by showing DIP switch configuration
  module.setDisplayToString(cur_display);
  delay(2000);
  module.setDisplayToString("--------");
}

unsigned char prevBtnState[8] = { 0, 0, 0, 0, 0, 0, 0, 0 };
unsigned char curBtnState[8] = { 0, 0, 0, 0, 0, 0, 0, 0 };
unsigned long lastBtnPress[8] = { MS_24H, MS_24H, MS_24H, MS_24H, MS_24H, MS_24H, MS_24H, MS_24H };

byte current_leds_state = 0; // for flashing between off and on
unsigned long leds_interval = 0;
byte led_state[8] = { 0, 0, 0, 0, 0, 0, 0, 0 };

void loop() {
  u8 midi_data[4] = {0, 0, 0, 0};
  u8 data_ptr = 0;

#ifdef ENABLE_MIDI
  USBMIDI.poll();
	while (USBMIDI.available()) {
		// We must read entire available data, so in case we receive incoming
		// MIDI data, the host wouldn't get stuck.
		u8 b = USBMIDI.read();
    midi_data[data_ptr++] = b;
	}
  if (data_ptr != 0 && debug_display) {
    char buf[9];
    sprintf(buf, "%02x %02x %02x", midi_data[0], midi_data[1], midi_data[2]);
    module.setDisplayToString(buf);
  }
  USBMIDI.flush();

  switch (midi_data[0]) {
    case 0xb0: // CC
      switch (midi_data[2]) {
        case 0:
          led_state[midi_data[1] - 1] = 0;
          break;
        case 2:
          led_state[midi_data[1] - 1] = 2;
          break;
        default:
          led_state[midi_data[1] - 1] = 1;
          break;
      }
      break;
    case 0xc0: // PC
      led_state[midi_data[1] - 1] = 2;
      break;
  }
#endif

  // Process expression pedal
  if (expression_pedal_enabled) {
    // Convert analog input range (1024) to MIDI (128 values)
    const unsigned char expression_value = map(analogRead(PIN_EXPRESSION_INPUT), 0, 1023, 0, 127);
    if (abs(last_expression_value - expression_value) > 5) {
      last_expression_value = expression_value;
#ifdef ENABLE_MIDI
      sendCC(CC_EXP_PEDAL, expression_value);
#endif
    }
  }

  // Process switches
  const byte keys = module.getButtons(); // order is not the same as on footpedal
  byte keystates[8] = { 0 };
  for (int i = 0; i < 8; i++) {
    keystates[KEYMAP[i]] = (keys & (1 << i)) ? 1 : 0;
  }

  /*char dbgbuf[9];
  sprintf(dbgbuf, "%u%u%u%u%u%u%u%u", keystates[0], keystates[1], keystates[2], keystates[3], keystates[4], keystates[5], keystates[6], keystates[7]);
  module.setDisplayToString(dbgbuf);*/

  const unsigned long now = millis();

  // Process key states and send MIDI CC
  for (int i = 0; i < 8; i++) { // logical buttons (order as on frontplate)
    if (keystates[i]) { // input is active (not debounced yet)
      if (prevBtnState[i] == 0 && now - lastBtnPress[i] > 100) { // from not pressed to pressed
        // send on release, not press (to make long-press possible)
        lastBtnPress[i] = now;
        prevBtnState[i] = 1;
      }
    } else {
      if (prevBtnState[i] == 1) { // was previously pressed
          if (now - lastBtnPress[i] > 1000) {
#ifdef ENABLE_MIDI
            sendCC(20 + i, 127);
#endif
          } else {
            if (i <= 4) { // bottom row
              if (switchmode_bottom == MIDI_CC_SEND_OFF_ON) {
                curBtnState[i] ^= 1;
              } else {
                curBtnState[i] = 1;
              }
            } else { // top row
              if (switchmode_top == MIDI_CC_SEND_OFF_ON) {
                curBtnState[i] ^= 1;
              } else {
                curBtnState[i] = 1;
              }
            }
#ifdef ENABLE_MIDI
            sendCC(10 + i, curBtnState[i] == 1 ? 127 : 0);
#endif
            if (internal_led_control) {
              led_state[i] = curBtnState[i] == 1 ? 1 : 0;
            }
          }
        prevBtnState[i] = 0;
      }
    }
  }

  // Set synchronized state for LED flashing
  if (now - leds_interval > 500) {
    current_leds_state ^= 1; // toggle
    leds_interval = now;
  }

  // Process incoming MIDI and set LEDs
  byte led_bitmap = 0;
  for (int i = 0; i < 8; i++) { // logical LEDs (order as on frontplate)
    if (led_state[i] == 0) { // turn off
      // nothing to do
    } else if (led_state[i] == 1) { // solid on
      led_bitmap |= 1 << LEDMAP[i];
    } else if (led_state[i] == 2) { // flashing
      if (current_leds_state == 1) {
        led_bitmap |= 1 << LEDMAP[i];
      } else {
        led_bitmap &= ~(1 << LEDMAP[i]);
      }
    }
  }
  module.setLEDs(led_bitmap);
}
