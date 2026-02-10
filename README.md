
## Front-End
Here's an example of how you can use `decluttering-card`, `auto-entities`, `button-card`, and `bubble-card` to create a dynamic chore dashboard in Home Assistant's Lovelace UI. 

```yaml
decluttering_templates:
  chore_section:
    card:
      type: conditional
      conditions:
        - condition: template
          value_template: |
            {{ expand(integration_entities('simplechores'))
               | selectattr('entity_id', 'search', '_status')
               | selectattr('state', 'eq', '[[state]]')
               | list
               | count > 0 }}
      card:
        type: vertical-stack
        cards:
          - type: custom:bubble-card
            card_type: separator
            name: '[[name]]'
            icon: '[[icon]]'
            sub_button:
              main: []
              bottom: []
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
          const base = entity.entity_id
            .replace(/(sensor\.|select\.)/, '')
            .replace('_status', '');

          const overdueId = `sensor.${base}_days_overdue`;
          const nextDueId = `sensor.${base}_next_due`;

          const overdue = states[overdueId];
          const nextDue = states[nextDueId];

          // Overdue case
          if (entity.state === 'overdue' && overdue) {
            const days = overdue.state;
            return days + " days overdue";
          }

          // Completed case → show due_in_days
          if (entity.state === 'completed' && nextDue && nextDue.attributes?.due_in_days !== undefined) {
            const days = nextDue.attributes.due_in_days;
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
                  const base = entity.entity_id.replace(/(sensor\.|select\.)/, '').replace('_status', '');
                  return `select.${base}_mark_completed_by`;
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
      - type: grid
        cards:
          - type: custom:bubble-card
            card_type: separator
            name: Overdue
            sub_button:
              main: []
              bottom: []
            icon: mdi:clipboard-alert
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
                  state: overdue
                  options:
                    type: custom:decluttering-card
                    template: chore_button
                    variables:
                      - entity: this.entity_id
          - type: custom:bubble-card
            card_type: separator
            name: Pending
            sub_button:
              main: []
              bottom: []
            icon: mdi:clipboard-list
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
                  state: pending
                  options:
                    type: custom:decluttering-card
                    template: chore_button
                    variables:
                      - entity: this.entity_id
          - type: custom:bubble-card
            card_type: separator
            name: Completed
            sub_button:
              main: []
              bottom: []
            icon: mdi:clipboard-check
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
                  state: completed
                  options:
                    type: custom:decluttering-card
                    template: chore_button
                    variables:
                      - entity: this.entity_id
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
  - path: choochoo2
    title: chores2
    type: sections
    sections:
      - type: grid
        cards:
          - type: custom:decluttering-card
            template: chore_section
            variables:
              - state: overdue
              - name: Overdue
              - icon: mdi:clipboard-alert
          - type: custom:decluttering-card
            template: chore_section
            variables:
              - state: pending
              - name: Pending
              - icon: mdi:clipboard-list
          - type: custom:decluttering-card
            template: chore_section
            variables:
              - state: completed
              - name: Completed
              - icon: mdi:clipboard-check

```