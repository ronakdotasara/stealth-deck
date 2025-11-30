/**
 * ============================================================================
 * @file state_machine.h
 * @brief State Machine Implementation
 * @version 1.0.0
 * @date 2025-11-30
 * @author Stealth Deck Project
 * @license MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * Generic state machine for managing application states and transitions.
 * 
 * Features:
 * - State transition management
 * - State entry/exit callbacks
 * - State history tracking
 * - Timeout-based state transitions
 * 
 * ============================================================================
 */

#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#include <Arduino.h>

// ============================================================================
// CONSTANTS
// ============================================================================

#define MAX_STATES 16
#define MAX_STATE_HISTORY 10

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

enum StateID {
    STATE_IDLE = 0,
    STATE_CALCULATOR,
    STATE_SMART_MODE,
    STATE_P2P_MODE,
    STATE_WIFI_SNIFFER,
    STATE_SETTINGS,
    STATE_PANIC,
    STATE_LOCKED,
    STATE_UNLOCKED,
    STATE_BOOT,
    STATE_ERROR
};

typedef void (*StateCallback)(void);

struct State {
    StateID id;
    const char* name;
    StateCallback onEnter;
    StateCallback onExit;
    StateCallback onUpdate;
    unsigned long timeout;
};

// ============================================================================
// CLASS DEFINITION
// ============================================================================

class StateMachine {
public:
    /**
     * @brief Constructor
     */
    StateMachine();
    
    /**
     * @brief Initialize state machine
     */
    void begin();
    
    /**
     * @brief Add a state to the state machine
     * 
     * @param id State ID
     * @param name State name
     * @param onEnter Callback when entering state
     * @param onExit Callback when exiting state
     * @param onUpdate Callback for state updates
     * @param timeout State timeout (0 = no timeout)
     * @return true if added successfully
     */
    bool addState(StateID id, const char* name, 
                  StateCallback onEnter = nullptr,
                  StateCallback onExit = nullptr,
                  StateCallback onUpdate = nullptr,
                  unsigned long timeout = 0);
    
    /**
     * @brief Transition to a new state
     * 
     * @param newState Target state ID
     * @return true if transition successful
     */
    bool transitionTo(StateID newState);
    
    /**
     * @brief Update current state
     * 
     * Should be called regularly from main loop
     */
    void update();
    
    /**
     * @brief Get current state ID
     * 
     * @return Current state ID
     */
    StateID getCurrentState() const { return _currentState; }
    
    /**
     * @brief Get previous state ID
     * 
     * @return Previous state ID
     */
    StateID getPreviousState() const;
    
    /**
     * @brief Get current state name
     * 
     * @return State name string
     */
    const char* getCurrentStateName() const;
    
    /**
     * @brief Check if in a specific state
     * 
     * @param state State ID to check
     * @return true if current state matches
     */
    bool isInState(StateID state) const { return _currentState == state; }
    
    /**
     * @brief Get time spent in current state
     * 
     * @return Time in milliseconds
     */
    unsigned long getStateTime() const;
    
    /**
     * @brief Print current state info
     */
    void printState() const;
    
    /**
     * @brief Print state history
     */
    void printHistory() const;

private:
    State _states[MAX_STATES];
    uint8_t _stateCount;
    
    StateID _currentState;
    StateID _previousState;
    StateID _stateHistory[MAX_STATE_HISTORY];
    uint8_t _historyIndex;
    
    unsigned long _stateEnterTime;
    
    /**
     * @brief Find state by ID
     * 
     * @param id State ID
     * @return Pointer to state or nullptr
     */
    State* findState(StateID id);
    
    /**
     * @brief Add state to history
     * 
     * @param state State ID
     */
    void addToHistory(StateID state);
};

#endif // STATE_MACHINE_H
