/** @file Observer.h
 * This file includes the base class of an observer for a two tank system with the water level of tank 1
 * as measurement value.
 */
#ifndef OBSERVER_H
#define OBSERVER_H

#include <vector>

/**
 * @brief Basis class of an observer implementation.
 */
class Observer {
protected:
    double dSampleTime = 0.0;       ///< Sample time in \f \si{\milli\second} \f
public:
    virtual ~Observer() = default;

    /**
     * Sets the initial state.
     * @param dInitialState vector with two starting values for the water levels of tank 1 and 2
     */
    virtual void setInitialState(std::vector<double> dInitialState) = 0;

    /**
     * Sets the observation gain.
     * @param dGain vector with two values for the gains
     */
    virtual void setGain(std::vector<double> dGain) = 0;

    /**
     * Computes the observer output at current time step for the given tank 1 height and the voltage of the
     * pump with the euler method
     *
     * @param dhT2 water level tank 2
     * @param dUa voltage of the pump
     * @return observed water levels of tank 1 and 2
     */
    virtual std::vector<double> compute(const double &dhT2,
                                        const double &dUa) = 0;
};

#endif // OBSERVER_H
