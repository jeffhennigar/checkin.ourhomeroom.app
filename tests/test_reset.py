from playwright.sync_api import sync_playwright, expect
import os

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Mock supabase CDN
        page.route("https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2", lambda route: route.fulfill(
            content_type="application/javascript",
            body="window.supabase = { createClient: () => ({ channel: () => ({ on: () => ({ subscribe: () => {} }) }) }) };"
        ))

        # Also mock any other external resources that might hang
        page.route("https://fonts.googleapis.com/**", lambda route: route.fulfill(body=""))
        page.route("https://fonts.gstatic.com/**", lambda route: route.fulfill(body=""))
        page.route("https://free.ourhomeroom.app/**", lambda route: route.fulfill(body=""))

        path = os.path.abspath("index.html")
        print(f"Navigating to file://{path}")
        # Use wait_until="domcontentloaded" to be faster and less prone to external resource hangs
        page.goto(f"file://{path}", wait_until="domcontentloaded")

        print("Testing reset_with_active_question...")
        page.evaluate("""() => {
            currentConfig = { type: 'text', question: 'What is 2+2?', isActive: true, isStarted: true };
            studentName = 'Test Student';
            selectedMcAnswer = 'A';
            document.getElementById('answer-text').value = '4';
            const btn = document.getElementById('btn-submit');
            btn.disabled = true;
            btn.innerHTML = 'Sending...';
            showStep('step-done');
        }""")

        expect(page.locator("#step-done")).to_have_class("step active")
        page.evaluate("resetForAnother()")

        selected_mc = page.evaluate("selectedMcAnswer")
        assert selected_mc == ''
        expect(page.locator("#answer-text")).to_have_value('')
        expect(page.locator("#btn-submit")).to_be_enabled()
        expect(page.locator("#btn-submit")).to_have_text('Send Answer 🎯')
        expect(page.locator("#step-question")).to_have_class("step active")
        expect(page.locator("#question-display")).to_have_text('What is 2+2?')
        print("reset_with_active_question passed!")

        print("Testing reset_without_active_question...")
        # Reset to done step again
        page.evaluate("""() => {
            currentConfig = { type: 'text', question: '', isActive: false, isStarted: false };
            selectedMcAnswer = 'B';
            document.getElementById('answer-text').value = 'some answer';
            const btn = document.getElementById('btn-submit');
            btn.disabled = true;
            btn.innerHTML = 'Sending...';
            showStep('step-done');
        }""")

        page.evaluate("resetForAnother()")

        selected_mc = page.evaluate("selectedMcAnswer")
        assert selected_mc == ''
        expect(page.locator("#answer-text")).to_have_value('')
        expect(page.locator("#btn-submit")).to_be_enabled()
        expect(page.locator("#step-waiting")).to_have_class("step active")
        print("reset_without_active_question passed!")

        browser.close()

if __name__ == "__main__":
    try:
        run_test()
        print("All tests passed successfully!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
