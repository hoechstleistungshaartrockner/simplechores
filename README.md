
## Front-End
Here's an example of how you can use `decluttering-card`, `auto-entities`, `button-card`, and `bubble-card` to create a dynamic chore dashboard in Home Assistant's Lovelace UI. 

```yaml
decluttering_templates:
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
          const base = entity.entity_id.replace(/(sensor\.|select\.)/, '').replace('_status', '');
          const overdueId = `sensor.${base}_days_overdue`;
          const overdue = states[overdueId];

          if (entity.state === 'overdue' && overdue) {
            const days = overdue.state;
            return days + " days overdue";
          }

          return entity.state + " ...";
        ]]]
      custom_fields:
        icon1:
          card:
            type: custom:button-card
            icon: mdi:broom
            styles:
              card:
                - background-color: rgba(255, 255, 255, 0.1)
                - width: 30px
                - height: 30px
              icon:
                - width: 18px
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
            - width: 24px
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
```