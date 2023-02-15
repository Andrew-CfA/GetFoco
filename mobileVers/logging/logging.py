"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version
"""

""" Logging handler for Get FoCo """

import logging

def initialize_logger(
        name,
        log_level: str = 'INFO',
        handlers = None,
        ) -> logging.Logger:
    
    """
    Initialize parameters for a logging object with a defined name. As part
    of the initialization, any current handlers will be removed and the
    logging level will be reset to the value of log_level.
    
    After initialization with this function, any subsequent loggers' name that
    starts with the base name in the hierarchy (e.g. for base name 'dashboard',
    a logger hierarchy such as 'dashboard.backend.get_user') will use the same
    parameters initialized here.
    
    For example:
        Initialization:
            logger = initialize_logger('dashboard', handlers=...)
            
        Usage (to use the same logging parameters):
            
            # Use built-in logging operators for usage
            logger = logging.getLogger('dashboard.backend')
            OR
            logger = logging.getLogger('dashboard.backend.get_user')
            OR
            logger = logging.getLogger('dashboard.views')

            logger.debug(msg, *args, **kwargs)
            logger.info(msg, *args, **kwargs)
            logger.warning(msg, *args, **kwargs)
            logger.error(msg, *args, **kwargs)
            logger.critical(msg, *args, **kwargs)
            

    Parameters
    ----------
    name : str
        Name of the logger to initialize. Use the base name (e.g. 'dashboard').
    log_level : str, optional
        The minimum message level to include in the log (following the levels
        at https://docs.python.org/3/library/logging.html#levels).
        The default is 'INFO'.        
    handlers : logging.handlers object or list of logging.handlers object
        Either a single or list of logging.handlers objects as defined in
        https://docs.python.org/3/library/logging.handlers.html. These can be
        stock or custom objects.        

    Raises
    ------
    TypeError
        TypeError is raised if any input is invalid (and includes a message
        specifying the input).

    Returns
    -------
    logging.Logger

    """
    
    # Ensure the inputs are the proper type. Don't check for logging.handlers
    # type here; it will be clear enough later if it's incorrect
    if not isinstance(str, name):
        raise TypeError("'name' input must be a string")
    if handlers is None:
        raise TypeError("At least one handler must be included")
        
    # Coerce handlers into a list
    if not isinstance(handlers, (list, tuple)):
        handlers = [handlers]

    logger = logging.getLogger(name=name)
    
    # Remove handler(s) if it already exists, then add the input handlers
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])
    
    # Ensure the specified logging level is an acceptable value and
    # (*critically*) convert to upper() (so that the expected integer is 
    # returned when setLevel() is called)
    log_level = log_level.upper()
    if log_level not in (
            'DEBUG',
            'INFO',
            'WARNING',
            'ERROR',
            'CRITICAL',
            ):
        raise TypeError("log_level is an invalid value")
        
    # Set new parameters
    logger.setLevel(log_level) # return the int from log_level        
            
    # Define the format string for use with all file and stream handlers
    formatStr = "%(asctime)s [%(levelname)s] %(name)s - {}%(message)s".format(
                    log_prepend,
                    )

    # Add each handler to the logger
    for hdlr in handlers:
        logger.addHandler(sh)

    # Initialize the log with the module base name (bottom of the hierarchy)
    logger.info(
        "Start from base directory '{modulename}' on {nm}".format(
            modulename=name.split('.')[0],
            )
        )

    return(logger)