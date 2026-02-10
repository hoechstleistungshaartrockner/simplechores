
## Front-End
Here's an example of how you can use `decluttering-card`, `auto-entities`, `button-card`, and `bubble-card` to create a dynamic chore dashboard in Home Assistant's Lovelace UI. 

### Related Entities Attribute
All chore entities now include a `related_entities` attribute containing the entity IDs of all related entities for that chore. This makes it easier to reference other entities without manually constructing entity IDs.

**Available in the `related_entities` attribute:**
- `status` - The status select entity (e.g., `select.kitchen_cleanup_status`)
- `assigned_to` - The assignee select entity (e.g., `select.kitchen_cleanup_assignee`)
- `mark_completed_by` - The completion select entity (e.g., `select.kitchen_cleanup_completed_by`)
- `points` - The points number entity (e.g., `number.kitchen_cleanup_points`)
- `days_overdue` - The days overdue sensor (e.g., `sensor.kitchen_cleanup_days_overdue`)
- `next_due` - The next due date sensor (e.g., `sensor.kitchen_cleanup_next_due`)

**Additional Attributes:**
- The `_status` select entity also includes the following attributes for convenient access:
  - `assigned_to` - The name of the currently assigned member
  - `next_due` - The next due date (ISO format string, e.g., "2026-02-15")
  - `due_in_days` - Number of days until the chore is due (negative if overdue)
  
  These attributes are automatically updated whenever the chore data changes.

**Example usage in templates:**
```yaml
# Access related entities from any chore entity
{{ state_attr('select.kitchen_cleanup_status', 'related_entities').days_overdue }}
# Returns: 'sensor.kitchen_cleanup_days_overdue'

# Get the assigned member directly from the status entity
{{ state_attr('select.kitchen_cleanup_status', 'assigned_to') }}
# Returns: 'John' (or the member's name)

# Get the next due date and days until due
{{ state_attr('select.kitchen_cleanup_status', 'next_due') }}
# Returns: '2026-02-15'

{{ state_attr('select.kitchen_cleanup_status', 'due_in_days') }}
# Returns: 5 (or negative if overdue)

# Use in automation
service: select.select_option
target:
  entity_id: "{{ state_attr('sensor.kitchen_cleanup_next_due', 'related_entities').mark_completed_by }}"
data:
  option: "John"
```

**Example in button-card JavaScript:**
```javascript
// Instead of manually constructing entity IDs:
const base = entity.entity_id.replace(/(sensor\.|select\.)/, '').replace('_status', '');
const overdueId = `sensor.${base}_days_overdue`;

// You can now use:
const overdueId = entity.attributes.related_entities.days_overdue;

// Access chore data directly from the status entity:
const assignedMember = entity.attributes.assigned_to;  // Returns: 'John'
const nextDue = entity.attributes.next_due;            // Returns: '2026-02-15'
const dueInDays = entity.attributes.due_in_days;       // Returns: 5 (or negative if overdue)
```

### Example Lovelace Configuration

```yaml
decluttering_templates:
  all_chore_state_sections:
    card:
      type: vertical-stack
      cards:
        - type: custom:decluttering-card
          template: chore_state_section
          variables:
            - user: '[[user]]'
            - state: "overdue"
            - icon: mdi:clipboard-alert
        - type: custom:decluttering-card
          template: chore_state_section
          variables:
            - user: '[[user]]'
            - state: "pending"
            - icon: mdi:clipboard-list
        - type: custom:decluttering-card
          template: chore_state_section
          variables:
            - user: '[[user]]'
            - state: "completed"
            - icon: mdi:clipboard-check
  chore_state_section:
    card:
      type: vertical-stack
      cards:
        - type: custom:bubble-card
          card_type: separator
          name: '[[state]]'
          sub_button:
            main: []
            bottom: []
          icon: '[[icon]]'
        - type: custom:auto-entities
          card:
            type: grid
            square: false
            columns: 2
          card_param: cards
          filter:
            include:
              - entity_id: '*_status'
                integration: simplechores
                state: '[[state]]'
                attributes: 
                  assigned_to: '[[user]]'
                options:
                  type: custom:decluttering-card
                  template: chore_button
                  variables:
                    - entity: this.entity_id
  chore_button:
    card:
      type: custom:button-card
      entity: '[[entity]]'
      show_name: true
      show_label: true
      show_state: false
      hold_action:
        action: more-info
      tap_action:
        action: call-service
        service: simplechores.toggle_chore
        service_data:
          member: |
            [[[
              return hass.user.name;
            ]]]
          entity_id: '[[entity]]'
      name: |
        [[[
          // Get the friendly name
          const full = entity.attributes.friendly_name || entity.entity_id;

          // Split into words
          const parts = full.split(" ");

          // Remove the last word (e.g., "Status")
          parts.pop();

          // Return the shortened name
          return parts.join(" ");
        ]]]
      label: |
        [[[
          // Now we can use the related_entities attribute instead of constructing IDs
          const relatedEntities = entity.attributes.related_entities || {};
          
          const overdueId = relatedEntities.days_overdue;
          const overdue = states[overdueId];

          // Overdue case
          if (entity.state === 'overdue' && overdue) {
            const overdue_days = overdue.state;
            return overdue_days + " days overdue";
          }

          // Completed case → show due_in_days
          if (entity.state === 'completed') {
            const days = entity.attributes.due_in_days;
            return `Due in ${days} days`;
          }

          // Default fallback
          return entity.state + " ...";
        ]]]


      custom_fields:
        icon1:
          card:
            type: custom:button-card
            icon: |
              [[[
                if (entity.state === 'completed') return 'mdi:checkbox-marked-outline';
                if (entity.state === 'pending') return 'mdi:checkbox-blank-outline';
                if (entity.state === 'overdue') return 'mdi:alert-decagram';
                return 'mdi:help-circle-outline';
              ]]]
            hold_action:
              action: more-info
              entity: |
                [[[
                  // Use related_entities instead of constructing the ID
                  const relatedEntities = entity.attributes.related_entities || {};
                  return relatedEntities.mark_completed_by;
                ]]]
            tap_action:
              action: call-service
              service: simplechores.toggle_chore
              service_data:
                member: |
                  [[[
                    return hass.user.name;
                  ]]]
                entity_id: '[[entity]]'
            styles:
              card:
                - background-color: rgba(255, 255, 255, 0.1)
                - width: 36px
                - height: 36px
              icon:
                - width: 24px
                - color: rgba(255, 255, 255, 0.8)
      styles:
        grid:
          - grid-template-areas: '". icon1" "n n" "l l"'
          - grid-template-rows: 24px 1fr 24px
          - grid-template-columns: 60% 40%
        card:
          - height: 100%
          - padding: 1rem
          - background: |
              [[[
                if (entity.state === 'pending') return "#215E61";
                if (entity.state === 'overdue') return "red";
                return "rgba(255, 255, 255, 0.1)";
              ]]]
        name:
          - text-align: left
          - font-size: 18px
          - font-weight: 500
          - justify-self: start
          - align-self: end
          - color: white
        label:
          - text-align: left
          - font-size: 12px
          - opacity: 0.7
          - justify-self: start
          - align-self: center
          - color: white
        custom_fields:
          icon1:
            - justify-self: end
            - width: 28px
            - color: white
views:
  - path: choochoo
    title: chores
    type: sections
    sections:
      - type: custom:simple-tabs
        tabs:
          - title: test
            icon: mdi:clipboard-list
            id: tab1
            card:
              type: custom:decluttering-card
              template: all_chore_state_sections
              variables:
                - user: "test"
          - title: Member 2
            icon: mdi:format-list-checkbox
            id: tab2
            card:
              type: custom:decluttering-card
              template: all_chore_state_sections
              variables:
                - user: "Member 2"
      - type: grid
        cards:
          - type: markdown
            content: >
              {% set metric = "points_earned_this_week" %}

              {% set unit = "pts" %}


              {# Use a namespace so we can mutate inside the loop #}

              {% set ns = namespace(items=[]) %}


              {# Collect entities with numeric value #}

              {% for e in states.sensor
                | selectattr("entity_id", "search", "_" ~ metric)
              %}
                {% set ns.items = ns.items + [{
                  "entity": e,
                  "value": e.state | float(0)
                }] %}
              {% endfor %}


              {# Sort by numeric value descending #}

              {% set sorted = ns.items | sort(attribute="value", reverse=true)
              %}


              # 🏆 Leaderboard — Current Week


              {% for item in sorted %}
                {% set e = item.entity %}
                {% set member = e.entity_id
                  | replace("sensor.", "")
                  | replace("_" ~ metric, "")
                %}
                **{{ loop.index }}. {{ member | capitalize }}** — {{ item.value }} {{ unit }}
              {% endfor %}


```