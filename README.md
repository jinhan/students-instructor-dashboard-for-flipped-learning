# Students and Instructor Dashboard for Flipped Learning

플립러닝의 온라인 학습 플랫폼으로 [Open edX platform](https://github.com/edx/edx-platform)을 사용하였습니다.<br>
학습자 화면의 progress 메뉴를 수정하여 학습자용 대시보드를 개발하였습니다.<br>
교수자 메뉴를 수정하여 교수자용 대시보드를 개발하여 학습자 진도 체크 및 응답 확인을 할 수 있도록 하였습니다. 

**시스템 구조**
![](https://user-images.githubusercontent.com/3071179/28836306-55dafe3e-7723-11e7-97e8-6f4b5ab123b2.png)

**학습자용 대시보드 (Open edX platform path)**
- lms > djangoapps > courseware > dashboard_data.py
- lms > djangoapps > courseware > grades.py
- lms > djangoapps > courseware > views.py
- lms > templates > courseware > progress.html
- lms > templates > courseware > upper_dashboard.js

**교수자용 대시보드 (Open edX platform path)**
- lms > djangoapps > instructor > views > instructor_dashboard.py
- lms > templates > instructor > instructor_dashboard_2 > instructor_dashboard_2.html
- lms > templates > instructor > instructor_dashboard_2 > dashboard.html
- lms > templates > instructor > instructor_dashboard_2 > dashboard.js

**학습자용 대시보드 화면**
![students](https://user-images.githubusercontent.com/3071179/28835846-c32b46f8-7721-11e7-8607-3d418be3593e.png)

**교수자용 대시보드 화면**
![instructor](https://user-images.githubusercontent.com/3071179/28835845-c2f8a680-7721-11e7-9043-73f2df442a27.png)
