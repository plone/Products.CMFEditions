Handle broken VersionPolicies and modifiers in a nicer way.

- ``ConditionalModifier.isApplicable``: return False when modifier is broken.
- ``portal_repository.listPolicies``: log and ignore Broken VersionPolicies.

[maurits]
