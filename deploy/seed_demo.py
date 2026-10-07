"""Populate an empty or partly populated deployment with fictional portfolio examples.

Run explicitly against the intended deployment. Existing records are left alone, and
matching demo records are reused when a previous run stopped partway through.
"""

import argparse
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request(base_url: str, method: str, path: str, body: dict | None = None):
    payload = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    call = Request(f"{base_url}/api/v1{path}", data=payload, headers=headers, method=method)
    try:
        with urlopen(call, timeout=20) as response:
            content = response.read()
            return json.loads(content) if content else None
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path}: HTTP {error.code}: {detail}") from error


def ensure(base_url: str, path: str, field: str, value: str, body: dict):
    existing = next(
        (entry for entry in request(base_url, "GET", path) if entry[field] == value), None
    )
    if existing is not None:
        return existing, False
    return request(base_url, "POST", path, body), True


def add_todo(base_url: str, project_id: str, title: str, module: str, status="open"):
    path = f"/projects/{project_id}/todos"
    ensure(
        base_url,
        path,
        "title",
        title,
        {"title": title, "module": module, "status": status},
    )


def add_backlog(
    base_url: str,
    project_id: str,
    title: str,
    description: str,
    priority="medium",
    section_id: str | None = None,
    done=False,
):
    path = f"/projects/{project_id}/backlog-items"
    if section_id is not None:
        path += f"?section_id={section_id}"
    body = {
        "title": title,
        "description": description,
        "priority": priority,
        "assignee": "Demo team",
        "section_id": section_id,
    }
    item, created = ensure(base_url, path, "title", title, body)
    if created and done:
        item = request(
            base_url,
            "PUT",
            f"/projects/{project_id}/backlog-items/{item['id']}",
            {**body, "status": "done"},
        )
    return item


def add_sprint(
    base_url: str,
    project_id: str,
    name: str,
    start: str,
    end: str,
    goal: str,
    items: list[dict],
    section_id: str | None = None,
    completed=False,
):
    path = f"/projects/{project_id}/sprints"
    if section_id is not None:
        path += f"?section_id={section_id}"
    sprint, created = ensure(
        base_url,
        path,
        "name",
        name,
        {
            "name": name,
            "start_date": start,
            "end_date": end,
            "goal": goal,
            "selected_item_ids": [item["id"] for item in items],
            "section_id": section_id,
        },
    )
    if created and completed:
        for item in items:
            request(
                base_url,
                "PUT",
                f"/projects/{project_id}/backlog-items/{item['id']}",
                {
                    "title": item["title"],
                    "description": item["description"],
                    "priority": item["priority"],
                    "status": "done",
                    "assignee": item["assignee"],
                    "section_id": section_id,
                },
            )
        request(
            base_url,
            "POST",
            f"/projects/{project_id}/sprints/{sprint['id']}/complete",
            {"section_id": section_id},
        )


def add_artifact(base_url: str, project_id: str, kind: str, content: dict):
    path = f"/projects/{project_id}/artifacts/{kind}"
    current = request(base_url, "GET", f"{path}/content")
    fields = ("nodes", "edges") if kind == "diagram" else ("strokes", "shapes", "images", "texts")
    if not any(current.get(field) for field in fields):
        request(base_url, "PUT", path, {"content": content})


def add_resource(base_url: str, project_id: str, title: str, target: str):
    ensure(
        base_url,
        f"/projects/{project_id}/resources",
        "title",
        title,
        {"title": title, "target": target, "kind": "web"},
    )


def add_link(base_url: str, source_id: str, target_id: str, relation: str, note: str):
    path = f"/projects/{source_id}/project-links"
    existing = request(base_url, "GET", path)
    if not any(
        link["target_id"] == target_id and link["relation"] == relation for link in existing
    ):
        request(
            base_url, "POST", path, {"target_id": target_id, "relation": relation, "note": note}
        )


def add_phase_task(base_url: str, phase_id: str, title: str, status: str):
    ensure(
        base_url,
        f"/phases/{phase_id}/tasks",
        "title",
        title,
        {"title": title, "assignee": "Demo team", "status": status},
    )


def populate(base_url: str):
    category_ids = {}
    for name in ("Experiences", "Delivery", "Experiments"):
        category, _ = ensure(base_url, "/project-categories", "name", name, {"name": name})
        category_ids[name] = category["id"]

    projects = {}
    examples = (
        (
            "Aurora Learning Hub",
            "Experiences",
            "agile",
            "active",
            None,
            "A fictional learning platform, from discovery to an accessible launch.",
            "2026-09-01",
            "2026-12-18",
        ),
        (
            "Inclusive Onboarding",
            "Experiences",
            "agile",
            "planned",
            "Aurora Learning Hub",
            "A child project for clear first steps and assistive technology support.",
            "2026-10-12",
            "2026-11-20",
        ),
        (
            "Harbor Wayfinding",
            "Delivery",
            "waterfall",
            "active",
            None,
            "A fictional city wayfinding rollout with phased delivery and handover.",
            "2026-08-17",
            "2027-01-29",
        ),
        (
            "Signal Garden",
            "Experiments",
            "custom",
            "active",
            None,
            "An interactive installation combining research, agile prototypes, and build phases.",
            "2026-09-14",
            "2027-02-12",
        ),
        (
            "Seasonal Data Stories",
            "Experiments",
            "custom",
            "completed",
            None,
            "A completed example showing an editorial brief and a published outcome.",
            "2026-04-06",
            "2026-08-28",
        ),
    )
    for title, category, method, status, parent, description, start, target in examples:
        project, _ = ensure(
            base_url,
            "/projects",
            "title",
            title,
            {
                "title": title,
                "category_id": category_ids[category],
                "planning_method": method,
                "status": status,
                "parent_id": projects[parent]["id"] if parent else None,
                "description": description,
                "owner": "Fictional demo team",
                "assignee": "Portfolio visitors",
                "start_date": start,
                "target_date": target,
                "notes": "Fictional portfolio data. Feel free to explore the views.",
            },
        )
        projects[title] = project

    aurora = projects["Aurora Learning Hub"]["id"]
    discovery = add_backlog(
        base_url,
        aurora,
        "Map learner journeys",
        "Interview three fictional learner groups and capture pain points.",
        "high",
    )
    add_sprint(
        base_url,
        aurora,
        "Discovery complete",
        "2026-09-07",
        "2026-09-18",
        "Agree on the first learning journey.",
        [discovery],
        completed=True,
    )
    search = add_backlog(
        base_url,
        aurora,
        "Search the course library",
        "Filter lessons by topic, difficulty, and duration.",
        "high",
    )
    progress = add_backlog(
        base_url, aurora, "Show learning progress", "Give learners a simple milestone view."
    )
    add_backlog(
        base_url,
        aurora,
        "Prepare launch checklist",
        "Review content, performance, and accessibility before launch.",
        "low",
    )
    add_sprint(
        base_url,
        aurora,
        "Learning flow",
        "2026-10-12",
        "2026-10-23",
        "Make courses easy to find and progress easy to understand.",
        [search, progress],
    )
    add_todo(base_url, aurora, "Review accessibility acceptance criteria", "overview")
    add_resource(
        base_url, aurora, "WCAG guidance", "https://www.w3.org/WAI/standards-guidelines/wcag/"
    )

    onboarding = projects["Inclusive Onboarding"]["id"]
    add_backlog(
        base_url,
        onboarding,
        "Build a welcome checklist",
        "A short path from first visit to the first completed lesson.",
        "high",
    )
    add_backlog(
        base_url,
        onboarding,
        "Test keyboard navigation",
        "Every setup step should work without a pointer.",
        "high",
    )
    add_todo(base_url, onboarding, "Write friendly empty states", "overview")

    harbor = projects["Harbor Wayfinding"]["id"]
    phase_details = (
        (
            "Planning",
            "Confirm routes, visitors, and placement constraints.",
            "completed",
            "2026-08-17",
            "2026-09-11",
            (("Interview visitors", "completed"), ("Approve route map", "completed")),
        ),
        (
            "Design",
            "Create a legible sign family for every decision point.",
            "in_progress",
            "2026-09-14",
            "2026-10-30",
            (
                ("Prototype directional signs", "completed"),
                ("Review contrast and type sizes", "in_progress"),
            ),
        ),
        (
            "Execution",
            "Fabricate and install the approved system.",
            "not_started",
            "2026-11-02",
            "2027-01-08",
            (("Confirm production partner", "not_started"),),
        ),
        (
            "Completion",
            "Inspect the route and hand over maintenance notes.",
            "not_started",
            "2027-01-11",
            "2027-01-29",
            (("Run final walk-through", "not_started"),),
        ),
    )
    phases = {
        phase["name"]: phase for phase in request(base_url, "GET", f"/projects/{harbor}/phases")
    }
    for name, description, status, start, end, tasks in phase_details:
        phase = phases[name]
        if not phase["description"]:
            request(
                base_url,
                "PUT",
                f"/projects/{harbor}/phases/{phase['id']}",
                {
                    "name": name,
                    "description": description,
                    "status": status,
                    "start_date": start,
                    "end_date": end,
                },
            )
        for title, task_status in tasks:
            add_phase_task(base_url, phase["id"], title, task_status)
    add_todo(base_url, harbor, "Confirm installation permit", "overview")
    add_resource(
        base_url, harbor, "Inclusive design principles", "https://designsystem.digital.gov/"
    )

    signal = projects["Signal Garden"]["id"]
    sections = {}
    for name, kind, description in (
        ("Research notes", "free", "Questions, observations, and decisions."),
        ("Interactive prototype", "agile", "Short experiments with visitor feedback."),
        ("Installation", "waterfall", "Preparation and physical delivery."),
    ):
        section, _ = ensure(
            base_url,
            f"/projects/{signal}/sections",
            "name",
            name,
            {"name": name, "section_type": kind, "description": description},
        )
        sections[name] = section["id"]
    research = sections["Research notes"]
    for title, status in (
        ("Observe visitor paths", "completed"),
        ("Compare quiet and busy hours", "in_progress"),
        ("Choose a story for the first installation", "not_started"),
    ):
        ensure(
            base_url,
            f"/sections/{research}/items",
            "title",
            title,
            {"title": title, "status": status, "assignee": "Demo team"},
        )
    prototype = sections["Interactive prototype"]
    sensor = add_backlog(
        base_url,
        signal,
        "Prototype a responsive light pattern",
        "React to movement without storing visitor data.",
        "high",
        prototype,
    )
    sound = add_backlog(
        base_url,
        signal,
        "Explore a quiet sound layer",
        "Keep the installation calm and optional.",
        "medium",
        prototype,
    )
    add_sprint(
        base_url,
        signal,
        "First interaction",
        "2026-10-19",
        "2026-10-30",
        "Test a welcoming interaction with a small group.",
        [sensor, sound],
        prototype,
    )
    installation = sections["Installation"]
    installation_phases = request(
        base_url, "GET", f"/projects/{signal}/phases?section_id={installation}"
    )
    add_phase_task(
        base_url, installation_phases[0]["id"], "Check power and mounting points", "in_progress"
    )
    add_todo(base_url, signal, "Sketch the visitor journey", "diagram")
    add_todo(base_url, signal, "Try two color palettes", "workspace")
    add_link(
        base_url,
        aurora,
        signal,
        "shares research with",
        "Both examples use short feedback loops to shape an accessible experience.",
    )

    stories = projects["Seasonal Data Stories"]["id"]
    editorial, _ = ensure(
        base_url,
        f"/projects/{stories}/sections",
        "name",
        "Editorial",
        {
            "name": "Editorial",
            "section_type": "free",
            "description": "A small finished example of the custom roadmap.",
        },
    )
    for title in ("Find a clear question", "Create charts", "Publish the story"):
        ensure(
            base_url,
            f"/sections/{editorial['id']}/items",
            "title",
            title,
            {"title": title, "status": "completed", "assignee": "Demo team"},
        )

    add_artifact(
        base_url,
        aurora,
        "diagram",
        {
            "version": 2,
            "nodes": [
                {
                    "id": "demo-aurora-discovery",
                    "label": "Discover learner needs",
                    "x": 60,
                    "y": 80,
                    "width": 180,
                    "height": 72,
                },
                {
                    "id": "demo-aurora-library",
                    "label": "Explore course library",
                    "x": 320,
                    "y": 80,
                    "width": 180,
                    "height": 72,
                },
                {
                    "id": "demo-aurora-progress",
                    "label": "Track progress",
                    "x": 580,
                    "y": 80,
                    "width": 180,
                    "height": 72,
                },
                {
                    "id": "demo-aurora-feedback",
                    "label": "Share feedback",
                    "x": 320,
                    "y": 260,
                    "width": 180,
                    "height": 72,
                },
            ],
            "edges": [
                ["demo-aurora-discovery", "demo-aurora-library"],
                ["demo-aurora-library", "demo-aurora-progress"],
                ["demo-aurora-progress", "demo-aurora-feedback"],
            ],
        },
    )
    add_artifact(
        base_url,
        signal,
        "workspace",
        {
            "version": 6,
            "strokes": [],
            "images": [],
            "shapes": [
                {
                    "id": "demo-signal-zone",
                    "kind": "rectangle",
                    "x": 45,
                    "y": 50,
                    "width": 260,
                    "height": 180,
                    "rotation": 0,
                    "color": "#527A8A",
                },
                {
                    "id": "demo-signal-light",
                    "kind": "ellipse",
                    "x": 390,
                    "y": 85,
                    "width": 150,
                    "height": 150,
                    "rotation": 0,
                    "color": "#DAB56C",
                },
            ],
            "texts": [
                {
                    "id": "demo-signal-note",
                    "text": "WELCOME AREA\nA calm first impression",
                    "x": 65,
                    "y": 75,
                    "width": 210,
                    "height": 100,
                    "color": "#F2F5F7",
                },
                {
                    "id": "demo-signal-question",
                    "text": "How does the garden respond?",
                    "x": 355,
                    "y": 265,
                    "width": 230,
                    "height": 90,
                    "color": "#DAB56C",
                },
            ],
        },
    )
    print("Demo portfolio ready: 3 categories, 5 projects, and sample plans, links, and visuals.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Deployment origin, without /api/v1")
    parser.add_argument("--apply", action="store_true", help="Write the fictional demo records")
    args = parser.parse_args()
    if not args.apply:
        parser.error("Pass --apply to create the demo records")
    populate(args.base_url.rstrip("/"))


if __name__ == "__main__":
    main()
