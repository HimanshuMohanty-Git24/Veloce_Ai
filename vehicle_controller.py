# vehicle_controller.py
import logging
import streamlit as st

class VehicleController:
    def __init__(self):
        self.lights_on = False
        self.doors_locked = False
        self.engine_on = False
        # Configure logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Add StreamHandler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def control_lights(self, command):
        if "on" in command.lower():
            if self.lights_on:
                log_msg = "🚗 Vehicle lights are already ON"
                self.logger.info(log_msg)
                st.write(f"Log: {log_msg}")
                return "Vehicle lights are already on"
            self.lights_on = True
            log_msg = "🚗 Vehicle lights turned ON"
            self.logger.info(log_msg)
            st.write(f"Log: {log_msg}")
            return "Vehicle lights have been turned on"
        elif "off" in command.lower():
            if not self.lights_on:
                log_msg = "🚗 Vehicle lights are already OFF"
                self.logger.info(log_msg)
                st.write(f"Log: {log_msg}")
                return "Vehicle lights are already off"
            self.lights_on = False
            log_msg = "🚗 Vehicle lights turned OFF"
            self.logger.info(log_msg)
            st.write(f"Log: {log_msg}")
            return "Vehicle lights have been turned off"
        return "Invalid lights command"

    def control_doors(self, command):
        if "lock" in command.lower() and "unlock" not in command.lower():
            if self.doors_locked:
                log_msg = "🚗 Vehicle doors are already LOCKED"
                self.logger.info(log_msg)
                st.write(f"Log: {log_msg}")
                return "All doors are already locked"
            self.doors_locked = True
            log_msg = "🚗 Vehicle doors LOCKED"
            self.logger.info(log_msg)
            st.write(f"Log: {log_msg}")
            return "All doors have been locked"
        elif "unlock" in command.lower():
            if not self.doors_locked:
                log_msg = "🚗 Vehicle doors are already UNLOCKED"
                self.logger.info(log_msg)
                st.write(f"Log: {log_msg}")
                return "All doors are already unlocked"
            self.doors_locked = False
            log_msg = "🚗 Vehicle doors UNLOCKED"
            self.logger.info(log_msg)
            st.write(f"Log: {log_msg}")
            return "All doors have been unlocked"
        return "Invalid door command"

    def control_engine(self, command):
        if "start" in command.lower():
            if self.engine_on:
                log_msg = "🚗 Engine is already RUNNING"
                self.logger.info(log_msg)
                st.write(f"Log: {log_msg}")
                return "Engine is already running"
            if not self.doors_locked:
                log_msg = "⚠️ Cannot start engine: Doors must be locked first"
                self.logger.warning(log_msg)
                st.write(f"Log: {log_msg}")
                return "Please lock the doors before starting the engine"
            self.engine_on = True
            log_msg = "🚗 Engine STARTED"
            self.logger.info(log_msg)
            st.write(f"Log: {log_msg}")
            return "Engine has been started"
        elif "stop" in command.lower() or "off" in command.lower():
            if not self.engine_on:
                log_msg = "🚗 Engine is already STOPPED"
                self.logger.info(log_msg)
                st.write(f"Log: {log_msg}")
                return "Engine is already stopped"
            self.engine_on = False
            log_msg = "🚗 Engine STOPPED"
            self.logger.info(log_msg)
            st.write(f"Log: {log_msg}")
            return "Engine has been stopped"
        return "Invalid engine command"