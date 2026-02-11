
# Home Assistant Simple Chores
A Home Assistant integration to manage and track household chores. It allows you to create chores, assign them to family members, set due dates.

>[!WARNING]
> This integration is still in development and may have bugs or incomplete features. Use with caution and report any issues you encounter.

## Features
- Create and manage chores with due dates, custom recurrency and assigned members.
- Track chore completion status (pending, completed, overdue).
- Assign Points to chores to balance workload among family members.
- Flexible dashboard configuration using decluttering-card and auto-entities card.

## Support Development
If you find this integration useful and want to support its development, please consider fueling me with a coffee! Your support helps me dedicate more time to improving the integration and adding new features. Thank you!
<a href="https://www.buymeacoffee.com/haartrockner" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-yellow.png" alt="Buy Me A Coffee" height="41" width="174"></a>


## Installation

### via HACS
1. Open Home Assistant and go to HACS.
2. Click the three-dot menu in the top right.
3. Select "Custom repositories".
4. In the "Repository" field, paste the URL of this repository (https://github.com/hoechstleistungshaartrockner/simplechores).
5. For "Category", select "Integration".
6. Click "Add".
7. Now go to the "Integrations" section in HACS, search for "Simple Chores", and click "Install".



### Example Dashboard Configuration

This code snippet demonstrates how to create a chore dashboard using the decluttering-card and auto-entities card. It organizes chores into sections based on their state (overdue, pending, completed) and allows users to toggle chore states directly from the dashboard.
**You need to adjust this code to fit your specific needs**. I guess the minimum would be to change the user variable.

To make this work, you need to install the following HACS plugins:

- decluttering-card
- auto-entities
- bubble-card
- simple-tabs
- button-card

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