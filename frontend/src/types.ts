export type SchemaModel = {
  id?: string;
  name?: string;
  title?: string;
  prefixes?: Record<string, string>;
  imports?: string[];
  default_prefix?: string;
  default_range?: string;
  classes: Record<string, SchemaClass>;
  slots: Record<string, Slot>;
  enums: Record<string, SchemaEnum>;
};

export type SchemaClass = {
  name?: string;
  description?: string;
  class_uri?: string;
  is_a?: string;
  slots?: string[];
};

export type Slot = {
  name?: string;
  description?: string;
  slot_uri?: string;
  range: string;
  required?: boolean;
  multivalued?: boolean;
};

export type SchemaEnum = {
  name?: string;
  permissible_values: Record<string, unknown> | string[];
};

export type SelectedItem =
  | { kind: 'class'; id: string }
  | { kind: 'slot'; id: string; classId?: string }
  | { kind: 'enum'; id: string }
  | null;
