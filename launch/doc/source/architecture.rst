Architecture of `launch`
========================

`launch` is designed to provide core features like describing actions (e.g. executing a process or including another launch description), generating events, introspecting launch descriptions, and executing launch descriptions.
While at the same time, it provides extension points so that the set of things on which these core features can operate on, or integrate with, can be expanded with additional packages.

Launch Descriptions
-------------------

The main actor object in `launch` is the :class:`launch.LaunchDescription`.

This class is responsible for capturing the system architect's (a.k.a. the user's) intent for how the system should be launched, as well as how `launch` itself should react to asynchronous events in the system during launch.

This class encapsulates the intent of the user as :class:`launch.ActionGroup`'s of discrete :class:`launch.Action`'s.
These actions can either be introspected for analysis without performing them, or the actions can be executed in response to an event in the launch system including the start of the launch process.

Additionally, launch descriptions, and the groups and actions which they contain, can have references to :class:`launch.Substitution`'s within them.
These substitutions are things which can be evaluated during launch and can be used to do various things like: get an launch argument, get an environment variable, or evaluate arbitrary Python expressions.

Launch descriptions, and the groups of actions contained therein, can either be introspected directly or launched by a :class:`launch.LaunchService`.
A launch service, is a long running activity which handles the event loop and dispatches actions.

Actions
-------

The aforementioned actions allow the user to express various intentions and the set of available actions to the user can also be extended by other packages, allowing for domain specific actions.

Actions can have direct side effects (e.g. run a process or set a configuration variable) and as well they can yield additional actions.
The latter can be used to create "syntactic sugar" actions which simply yield more verbose actions.

Actions may also have :class:`launch.ActionConfiguration`'s, which can affect the behavior of the actions.
These configurations are where :class:`launch.Substitution`'s can be used to provide more flexibility when describing reusable launch descriptions.

Basic Actions
^^^^^^^^^^^^^

`launch` provides the foundational actions on which other more sophisticated actions may be built:

- :class:`launch.actions.IncludeLaunchDescription`

  - This action will include another launch description as if it had been copy-pasted to the location of the include action.

- :class:`launch.actions.SetLaunchConfiguration`

  - This action will set a :class:`launch.LaunchConfiguration` to a specified value, creating it if it doesn't already exist.
  - These launch configurations can be accessed by any action via a substitution, but are scoped by default.

- :class:`launch.actions.DeclareLaunchDescriptionArgument`

  - This action will declare a launch description argument, which can have a name, default value, and documentation.
  - The argument will be exposed via a command line option for a root launch description, or as action configurations to the include launch description action for the included launch description.

- :class:`launch.actions.SetEnvironmentVariable`

  - This action will set an environment variable by name.

- :class:`launch.actions.ExecuteProcess`

  - This action will execute a process given it's path and arguments, and optionally other things like working directory or environment variables.

- :class:`launch.actions.RegisterEventHandler`

  - This action will register a :class:`launch.EventHandler` class, which takes user defined lambda to handle some event.
  - It could be any event, a subset of events, or one specific event.

- :class:`launch.actions.UnregisterEventHandler`

  - This action will remove a previously registered event.

- :class:`launch.actions.EmitEvent`

  - This action will emit an :class:`launch.Event` based class, causing all registered event handlers that match it to be called.

- :class:`launch.actions.RaiseError`

  - This action will stop execution of the launch system and provide a user defined error message.

More actions can always be defined via extension, and there may even be additional actions defined by `launch` itself, but they are more situational and would likely be built on top of the above actions anyways.

Base Action
^^^^^^^^^^^

All actions need to be based on the :class:`launch.Action` base class, so that some common interface is available to the launch system when interacting with actions defined by external packages.
Since the base action class is a first class element in a launch description it also inherits from :class:`launch.LaunchDescriptionEntity`, which is the polymorphic type used when iterating over the elements in a launch description.

Also, the base action has a few features common to all actions like some introspection utilities, the ability to have :class:`launch.ActionConfiguration`'s, and the ability to be associated with a single :class:`launch.Conditional`, like the :class:`launch.IfCondition` class or the :class:`launch.UnlessCondition` class.

The action configurations are supplied when the user uses an action and can be used to pass "arguments" to the action in order to influence its behavior, e.g. this is how you would pass the path to the executable in the execute process action.

If an action is associated with a condition, that condition is evaluated to determine if the action is executed or not.
Even if the associated action evaluates to false the action will be available for introspection.

Action Groups
-------------

Actions may be grouped for various reasons:

- to conditionally include a group of actions
- to "push and pop" state changes due to actions, like setting a launch configuration
- for organizational purposes

So a :class:`launch.ActionGroup` contains zero to many actions, may be conditionally evaluated using :class:`launch.IfCondition` or :class:`launch.UnlessCondition`, and may optionally scope changes to state.

Since an action group is a first class element in a launch description it also inherits from :class:`launch.LaunchDescriptionEntity`, just like the action base class.

Substitutions
-------------

A substitution is a something that cannot or should not be evaluated until it's time to execute the launch description that they are used in.
There are many possible variations of a substitution, but here are some of the core ones implemented by `launch` (all of which inherit from :class:`launch.Substitution`):

- :class:`launch.substitutions.Text`

  - This substitution simply returns the given string when evaluated.
  - It is usually used to wrap literals in the launch description so they can be concatenated with other substitutions.

- :class:`launch.substitutions.PythonExpression`

  - This substitution will evaluate a python expression and get the result as a string.

- :class:`launch.substitutions.LaunchConfiguration`

  - This substitution gets a launch configuration value, as a string, by name.

- :class:`launch.substitutions.LaunchDescriptionArgument`

  - This substitution gets the value of a launch description argument, as a string, by name.

- :class:`launch.substitutions.EnvironmentVariable`

  - This substitution gets an environment variable value, as a string, by name.

The base substitution class provides some common introspection interfaces (which the specific derived substitutions may influence).

The Launch Service
------------------

The launch service is responsible for processing emitted events, dispatching them to event handlers, and executing actions as needed.
The launch service offers three main services:

- include a launch description

  - can be called from any thread

- run event loop
- shutdown

  - cancels any running actions and event handlers
  - then breaks the event loop if running
  - can be called from any thread

A typical use case would be:

- create a launch description (programmatically or based on a markup file)
- create a launch service
- include the launch description in the launch service
- add a signal handler for SIGINT that calls shutdown on the launch service
- run the event loop on the launch service

Additionally you could host some SOA (like REST, SOAP, ROS Services, etc...) server in another thread, which would provide a variety of services, all of which would end up including a launch description in the launch service asynchronously or calling shutdown on the launch service asynchronously.
Remember that a launch description can contain actions to register event handlers, emit events, run processes, etc.
So being able to include arbitrary launch descriptions asynchronously is the only feature you require to do most things dynamically while the launch service is running.

Extension Points
----------------

In order to allow customization of how `launch` is used in specific domains, extension of the core categories of features is provided.
External Python packages, through extension points, may add:

- new actions

  - must directly or indirectly inherit from :class:`launch.Action`

- new events

  - must directly or indirectly inherit from :class:`launch.Event`

- new substitutions

  - must directly or indirectly inherit from :class:`launch.Substitution`

- kinds of entities in the launch description

  - must directly or indirectly inherit from :class:`launch.LaunchDescriptionEntity`
