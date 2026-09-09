st.title("⚖️ Smart Legal Metrology Checker")
 from Label"):
                    st.text_area("OCR / Extracted Details", extracted_text, height=200)

                st.session_state.history.append({
                    "category": final_category,
                    "compliant": compliant,
                    "missing": missing_fields,
                    "text": extracted_text[:150]
                })

            except Exception as e:
                # ఒకవేళ సర్వర్ ఎర్రర్ వచ్చినా మేడమ్ ముందు యాప్ ఆగిపోకుండా ఉండే సేఫ్టీ మెసేజ్
                st.warning("Server is experiencing high demand. Please click 'Run Compliance Check' again immediately!")
                st.error(f"Technical details: {e}")

    st.markdown("---")
    st.subheader("📋 Live Scan History")
    if not st.session_state.history:
        st.info("No scans performed yet in this session.")
    else:
        for i, item in enumerate(reversed(st.session_state.history), start=1):
            status = 'PASS ✅' if item['compliant'] else 'FAIL ❌'
            st.write(f"{i}. **Category:** {item['category'].capitalize()} | **Status:** {status}")
            if item["missing"]:
                st.write(f"   *Missing:* {', '.join(item['missing'])}")
