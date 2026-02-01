import json
import os
from datetime import datetime, date
from collections import defaultdict
import csv

class SmartTimetable:
    def __init__(self):
        self.data_file = "data/exams.json"
        self.progress_file = "data/progress.json"
        self.setup_data_files()
    
    def setup_data_files(self):
        """Create data directory and files if they don't exist"""
        os.makedirs("data", exist_ok=True)
        
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)
        
        if not os.path.exists(self.progress_file):
            with open(self.progress_file, 'w') as f:
                json.dump({}, f)
    
    def add_exam(self):
        """Add a new exam"""
        print("\n" + "="*50)
        print("ADD NEW EXAM")
        print("="*50)
        
        subject = input("Subject name: ").strip()
        
        while True:
            exam_date = input("Exam date (YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(exam_date, "%Y-%m-%d")
                break
            except ValueError:
                print("Invalid date format. Use YYYY-MM-DD")
        
        daily_hours = float(input("Daily study hours: ").strip())
        total_units = int(input("Total units/chapters: ").strip())
        
        exam = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "subject": subject,
            "exam_date": exam_date,
            "daily_hours": daily_hours,
            "total_units": total_units,
            "created_at": date.today().isoformat()
        }
        
        # Load existing exams
        with open(self.data_file, 'r') as f:
            exams = json.load(f)
        
        exams.append(exam)
        
        # Save back
        with open(self.data_file, 'w') as f:
            json.dump(exams, f, indent=2)
        
        print(f"\n✓ Exam '{subject}' added successfully!")
    
    def calculate_days_left(self, exam_date_str):
        """Calculate days remaining until exam"""
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        today = date.today()
        return (exam_date - today).days
    
    def show_countdown(self):
        """Display countdown for all exams"""
        print("\n" + "="*50)
        print("COUNTDOWN TIMER")
        print("="*50)
        
        with open(self.data_file, 'r') as f:
            exams = json.load(f)
        
        if not exams:
            print("No exams added yet!")
            return
        
        for exam in exams:
            days_left = self.calculate_days_left(exam['exam_date'])
            print(f"\n📚 {exam['subject']}:")
            print(f"   ⏳ {days_left} days left")
            print(f"   📅 Exam Date: {exam['exam_date']}")
            print(f"   🕐 Daily Hours: {exam['daily_hours']}")
            
            if days_left <= 0:
                print("   ⚠️  Exam is today or has passed!")
    
    def get_daily_suggestion(self):
        """Generate today's study suggestion"""
        print("\n" + "="*50)
        print("TODAY'S STUDY PLAN")
        print("="*50)
        
        with open(self.data_file, 'r') as f:
            exams = json.load(f)
        
        with open(self.progress_file, 'r') as f:
            progress = json.load(f)
        
        if not exams:
            print("No exams added yet!")
            return
        
        today = date.today().isoformat()
        
        for exam in exams:
            days_left = self.calculate_days_left(exam['exam_date'])
            
            if days_left > 0:
                exam_id = exam['id']
                completed = progress.get(exam_id, {}).get('completed_units', [])
                total_units = exam['total_units']
                
                # Calculate units per day
                units_per_day = max(1, total_units // max(1, days_left))
                
                # Find next unit to study
                next_unit = 1
                for unit in range(1, total_units + 1):
                    if unit not in completed:
                        next_unit = unit
                        break
                
                print(f"\n📚 {exam['subject']}:")
                print(f"   ✅ Study: Unit {next_unit}")
                print(f"   📖 Additional: MCQs/Revision of Unit {max(1, next_unit-1)}")
                print(f"   ⏰ Time: {exam['daily_hours']} hours")
                print(f"   📊 Progress: {len(completed)}/{total_units} units")
    
    def track_progress(self):
        """Update progress for an exam"""
        print("\n" + "="*50)
        print("UPDATE PROGRESS")
        print("="*50)
        
        with open(self.data_file, 'r') as f:
            exams = json.load(f)
        
        if not exams:
            print("No exams added yet!")
            return
        
        print("\nSelect exam:")
        for i, exam in enumerate(exams, 1):
            print(f"{i}. {exam['subject']}")
        
        try:
            choice = int(input("\nEnter exam number: ")) - 1
            if 0 <= choice < len(exams):
                exam = exams[choice]
                
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                
                exam_id = exam['id']
                if exam_id not in progress:
                    progress[exam_id] = {
                        'completed_units': [],
                        'last_updated': None
                    }
                
                print(f"\nExam: {exam['subject']}")
                print(f"Total Units: {exam['total_units']}")
                
                # Show completed units
                completed = progress[exam_id]['completed_units']
                if completed:
                    print(f"Completed: {', '.join(map(str, sorted(completed)))}")
                
                # Mark units as complete
                print("\nEnter unit numbers to mark as complete (comma-separated):")
                print("Example: 1,2,3 or 'all' for all units")
                
                units_input = input("Units: ").strip().lower()
                
                if units_input == 'all':
                    completed = list(range(1, exam['total_units'] + 1))
                else:
                    try:
                        new_units = [int(u.strip()) for u in units_input.split(',')]
                        for unit in new_units:
                            if 1 <= unit <= exam['total_units'] and unit not in completed:
                                completed.append(unit)
                    except ValueError:
                        print("Invalid input!")
                
                # Update progress
                progress[exam_id]['completed_units'] = list(set(completed))
                progress[exam_id]['last_updated'] = date.today().isoformat()
                
                # Save progress
                with open(self.progress_file, 'w') as f:
                    json.dump(progress, f, indent=2)
                
                # Calculate percentage
                percentage = (len(completed) / exam['total_units']) * 100
                print(f"\n✓ Progress updated!")
                print(f"📊 Completion: {percentage:.1f}% ({len(completed)}/{exam['total_units']} units)")
            
        except (ValueError, IndexError):
            print("Invalid selection!")
    
    def export_to_csv(self):
        """Export study plan to CSV"""
        print("\n" + "="*50)
        print("EXPORT STUDY PLAN")
        print("="*50)
        
        with open(self.data_file, 'r') as f:
            exams = json.load(f)
        
        with open(self.progress_file, 'r') as f:
            progress = json.load(f)
        
        if not exams:
            print("No exams to export!")
            return
        
        filename = f"study_plan_{date.today().isoformat()}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Subject', 'Exam_Date', 'Days_Left', 'Total_Units', 
                         'Completed_Units', 'Progress_%', 'Daily_Hours']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for exam in exams:
                exam_id = exam['id']
                completed = progress.get(exam_id, {}).get('completed_units', [])
                days_left = self.calculate_days_left(exam['exam_date'])
                
                writer.writerow({
                    'Subject': exam['subject'],
                    'Exam_Date': exam['exam_date'],
                    'Days_Left': days_left,
                    'Total_Units': exam['total_units'],
                    'Completed_Units': len(completed),
                    'Progress_%': (len(completed) / exam['total_units'] * 100) if exam['total_units'] > 0 else 0,
                    'Daily_Hours': exam['daily_hours']
                })
        
        print(f"\n✓ Study plan exported to '{filename}'")
        print(f"📁 File saved in current directory")
    def delete_exam(self):
     print("\n" + "="*50)
     print("DELETE EXAM")
     print("="*50)

     with open(self.data_file, 'r') as f:
        exams = json.load(f)

     if not exams:
        print("No exams to delete!")
        return

     for i, exam in enumerate(exams, 1):
        print(f"{i}. {exam['subject']}")

     try:
        choice = int(input("\nEnter exam number to delete: ")) - 1
        if 0 <= choice < len(exams):
            removed = exams.pop(choice)

            with open(self.data_file, 'w') as f:
                json.dump(exams, f, indent=2)

            print(f"\n✓ Deleted exam: {removed['subject']}")
     except:
     
        print("Invalid input!")

    def todays_reminders(self):
    
        print("\n" + "="*50)
        print("📌 TODAY'S REMINDERS")
        print("="*50)

        with open(self.data_file, 'r') as f:
            exams = json.load(f)

        with open(self.progress_file, 'r') as f:
            progress = json.load(f)

        if not exams:
            print("No exams added yet!")
            return

        today = date.today().isoformat()
        reminders_found = False

        for exam in exams:
            days_left = self.calculate_days_left(exam['exam_date'])
            if days_left > 0:
                exam_id = exam['id']
                completed = progress.get(exam_id, {}).get('completed_units', [])
                total_units = exam['total_units']

            # Determine which units to study today
                units_per_day = max(1, total_units // max(1, days_left))
                units_to_study = []

                for unit in range(1, total_units + 1):
                    if unit not in completed and len(units_to_study) < units_per_day:
                       units_to_study.append(unit)

                if units_to_study:
                    reminders_found = True
                    print(f"\n📚 {exam['subject']} (Exam in {days_left} days):")
                    print(f"   ⏰ Study units today: {', '.join(map(str, units_to_study))}")
                    print(f"   🕐 Daily study hours: {exam['daily_hours']}")

        if not reminders_found:
            print("✅ All exams completed or no study scheduled for today!")

    def run(self):
        """Main application loop"""
        while True:
            print("\n" + "="*50)
            print("📚 SMART TIMETABLE APP")
            print("="*50)
            print("1. Add Exam")
            print("2. View Countdown")
            print("3. Get Today's Study Suggestion")
            print("4. Track Progress")
            print("5. Export to CSV")
            print("6. Delete Exam")
            print("7. Today's Reminders")
            print("8. Exit")
            print("="*50)
            
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
             self.add_exam()
            elif choice == '2':
             self.show_countdown()
            elif choice == '3':
             self.get_daily_suggestion()
            elif choice == '4':
             self.track_progress()
            elif choice == '5':
             self.export_to_csv()
            elif choice == '6':
             self.delete_exam()
            elif choice == '7':
             self.todays_reminders()
            elif choice == '8':
             print("\n👋 Goodbye! Happy studying!")
             break
            else:
             print("Invalid choice! Please enter 1-8.")
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    app = SmartTimetable()
    app.run() 
