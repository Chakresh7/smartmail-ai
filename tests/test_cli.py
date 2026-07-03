from src.cli import main


def test_cli_sample():
    rc = main(["--sample"])
    assert rc == 0


def test_cli_email_file(tmp_path):
    sample = {
        "email_id": "t1",
        "thread_id": "t1",
        "subject": "hi",
        "sender": "a@b.com",
        "sender_name": "A",
        "to": ["me@x.com"],
        "cc": [],
        "bcc": [],
        "body": "Hello",
        "html_body": None,
        "received_at": "2026-01-01T00:00:00",
        "is_reply": False,
        "labels": [],
        "attachments": [],
    }
    p = tmp_path / "e.json"
    import json
    p.write_text(json.dumps(sample))
    rc = main(["--email-file", str(p)])
    assert rc == 0
