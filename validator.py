import copy
import eve.io.mongo
from collections import Sequence
class Validator(eve.io.mongo.Validator):
    def validate_field(self, field, value, schema=None):
        schema = schema is None and self.schema or schema
        if self.ignore_none_values and value is None:
            return

        definition = schema.get(field)
        if definition:
            self.check_definition(definition, field, value)

    def check_definition(self, definition, field, value):
        if value is None:
            if definition.get("nullable", False) is True:
                return
            else:
                self._error(field, errors.ERROR_NOT_NULLABLE)

        if 'type' in definition:
            self._validate_type(definition['type'], field, value)
            if self.errors.get(field):
                return

        if "dependencies" in definition:
            self._validate_dependencies(
                document=document,
                dependencies=definition["dependencies"],
                field=field
            )
            if self.errors.get(field):
                return

        definition_rules = [rule for rule in definition.keys()
                            if rule not in self.special_rules]
        for rule in definition_rules:
            check_rule(rule, field, value)

    def check_rule(self, rule, field, value):
        validatorname = "_validate_" + rule.replace(" ", "_")
        validator = getattr(self, validatorname, None)
        if validator:
            validator(definition[rule], field, value)
        else:
            if not self.allow_unknown:
                self._error(field, errors.ERROR_UNKNOWN_FIELD)

    def _validate_or(self, definitions, field, value):
        results = []
        validator = copy.copy(self)
        for definition in definitions:
            validator.schema = {field: definition}
            results.append(validator.validate({field: value}, context=self.document))
        if not any(results):
            self._error(field, "{field} must match one of: {definitions}".format(
                field=field,
                definitions=str(definitions)))
        
