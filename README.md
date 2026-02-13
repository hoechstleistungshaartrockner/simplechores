
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
7. in HACS, search for "Simple Chores", and click "Download".
8. Go to "Configuration" → "Integrations" in Home Assistant.
9. Click the "+" button to add a new integration.
10. Search for "Simple Chores" and follow the prompts to set it up.
11. To add your first chore, click on the gear icon of the integration in the "Integrations" page, and click "Manage Chores". From there, you can create and manage your chores.


## Created Devices and Entities
In this integration, "Members" and "Chores" are the two main concepts. For both of these, the integration creates a device and multiple entities to represent their state.
Here's a breakdown of the created entities and their attributes for both Members and Chores:

### Member Entities

Member names are sanitized (lowercased, spaces replaced with underscores) for use in entity IDs. For example, a member named "John Doe" would have entity IDs like `sensor.john_doe_points_earned_today`.

**Points Tracking Sensors** (tracks points earned from completed chores):
- `sensor.{member_name}_points_earned_today`
  - State: numeric value, total points earned today
  - Unit: configurable points label (default: "points")
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device

- `sensor.{member_name}_points_earned_this_week`
  - State: numeric value, total points earned this week (starting Monday)
  - Unit: configurable points label (default: "points")
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device

- `sensor.{member_name}_points_earned_this_month`
  - State: numeric value, total points earned this month
  - Unit: configurable points label (default: "points")
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device

- `sensor.{member_name}_points_earned_this_year`
  - State: numeric value, total points earned this year
  - Unit: configurable points label (default: "points")
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device

**Chore Completion Tracking Sensors** (tracks number of chores completed):
- `sensor.{member_name}_chores_completed_today`
  - State: numeric value, number of chores completed today
  - Unit: "chores"
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device

- `sensor.{member_name}_chores_completed_this_week`
  - State: numeric value, number of chores completed this week
  - Unit: "chores"
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device

- `sensor.{member_name}_chores_completed_this_month`
  - State: numeric value, number of chores completed this month
  - Unit: "chores"
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device

- `sensor.{member_name}_chores_completed_this_year`
  - State: numeric value, number of chores completed this year
  - Unit: "chores"
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device

**Status Sensors** (current state):
- `sensor.{member_name}_chores_pending`
  - State: numeric value, number of pending chores currently assigned to member
  - Unit: "chores"
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device

- `sensor.{member_name}_chores_overdue`
  - State: numeric value, number of overdue chores currently assigned to member
  - Unit: "chores"
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device

- `sensor.{member_name}_assigned_chore_entities`
  - State: numeric value, total count of chores assigned to member
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the member device
    - `entity_ids`: list of status entity IDs for all chores assigned to this member (useful for automations and dashboard filtering)

### Chore Entities

Each chore is assigned a unique `chore_id` in the format `{sanitized_chore_name}_{timestamp}` (e.g., `take_out_trash_1707685200`). All entity IDs for a chore use this chore_id as their base.

- `select.{chore_id}_status`
  - State: "pending", "completed", or "overdue"
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the chore device
    - `chore_id`: unique identifier for the chore
    - `chore_name`: display name of the chore
    - `assigned_to`: member name the chore is assigned to (if any)
    - `due_date`: ISO date string of next due date
    - `due_in_days`: number of days until due (can be negative if overdue)
    - `area_id`: Home Assistant area ID (UUID) if chore is assigned to an area
    - `area_name`: human-readable area name (e.g., "Living Room") if chore is assigned to an area
    - `related_entities`: dictionary of related entity IDs for this chore

- `select.{chore_id}_assigned_to`
  - State: name of the member assigned to the chore
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the chore device
    - `chore_id`: unique identifier for the chore
    - `chore_name`: display name of the chore
    - `related_entities`: dictionary of related entity IDs for this chore

- `select.{chore_id}_mark_completed_by`
  - State: null (this is an action trigger entity)
  - Purpose: Select a member to mark the chore as completed by that member (awards points and updates counters)
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the chore device
    - `chore_id`: unique identifier for the chore
    - `chore_name`: display name of the chore
    - `related_entities`: dictionary of related entity IDs for this chore

- `number.{chore_id}_points`
  - State: numeric value representing points awarded for completing this chore
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the chore device
    - `chore_id`: unique identifier for the chore
    - `chore_name`: display name of the chore
    - `related_entities`: dictionary of related entity IDs for this chore

- `date.{chore_id}_due_date`
  - State: date value of next due date (user-adjustable)
  - Purpose: Allows users to manually set/adjust the next due date for the chore
  - Attributes:
    - `integration`: "simplechores"
    - `device_id`: Home Assistant device ID for the chore device
    - `chore_id`: unique identifier for the chore
    - `chore_name`: display name of the chore
    - `recurrence_pattern`: pattern for chore recurrence (e.g., "daily", "weekly")
    - `recurrence_interval`: interval for recurrence (numeric)
    - `last_completed`: ISO date string of when chore was last completed
    - `due_in_days`: number of days until due (can be negative if overdue)
    - `status`: current status (pending/completed/overdue)
    - `assigned_to`: member name the chore is assigned to (if any)
    - `related_entities`: dictionary of related entity IDs for this chore

## Example Dashboard Configuration

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
            - state: overdue
            - icon: mdi:clipboard-alert
        - type: custom:decluttering-card
          template: chore_state_section
          variables:
            - user: '[[user]]'
            - state: pending
            - icon: mdi:clipboard-list
        - type: custom:decluttering-card
          template: chore_state_section
          variables:
            - user: '[[user]]'
            - state: completed
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
      styles:
        grid:
          - grid-template-areas: '"area icon1" "n n" "l l"'
          - grid-template-rows: 18px 1fr 24px
          - grid-template-columns: 60% 40%
        card:
          - height: 100%
          - padding: 1rem
          - background: |
              [[[
                if (entity.state === 'pending') return "#215E61";
                if (entity.state === 'overdue') return "#820300";
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
          area:
            - justify-self: start
            - align-self: start
            - font-size: 14px
            - font-weight: 500
          icon1:
            - justify-self: end
            - width: 28px
            - color: white
      name: |
        [[[
          const full = entity.attributes.friendly_name || entity.entity_id;
          const parts = full.split(" ");
          parts.pop();
          return parts.join(" ");
        ]]]
      label: |
        [[[
          if (entity.state === 'overdue') {
            return entity.attributes.due_in_days + " days overdue";
          }
          if (entity.state === 'completed') {
            return `Due in ${entity.attributes.due_in_days} days`;
          }
          return entity.state + " ...";
        ]]]
      custom_fields:
        area: |
          [[[
            return entity.attributes.area_name
          ]]]
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
                  const related = entity.attributes.related_entities || {};
                  return related.mark_completed_by;
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
                - user: test
          - title: Member 2
            icon: mdi:format-list-checkbox
            id: tab2
            card:
              type: custom:decluttering-card
              template: all_chore_state_sections
              variables:
                - user: Member 2
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