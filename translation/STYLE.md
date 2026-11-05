# MLB 2K6 (PS2) 한글화 번역 지침

## 출력 형식
- 입력: `src/batches/<묶음>_<번호>.json` = `[{"i": 번호, "en": 원문, "max": 허용 길이(있을 때만), "unit": "char"|"byte"}]`
- 출력: `tr/<묶음>_<번호>.json` = `{"<i>": "번역문", ...}` (UTF-8 JSON, 키는 문자열로 된 i)
  - 번역하지 않고 원문을 그대로 둘 항목은 `null`
- 모든 항목에 대해 키를 빠짐없이 출력한다 (null 포함).

## 길이 제한 (반드시 지킬 것)
- `"unit": "char"` → 번역문 글자 수(공백·기호 포함, 한글 1글자=1) ≤ `max`
- `"unit": "byte"` → 한글 음절 1개 = 2바이트, 영문·숫자·공백·기호 = 1바이트로 센 합계 ≤ `max`
- `max` 가 없으면 제한 없음(그래도 원문보다 지나치게 길게 쓰지 않는다).
- 넘칠 것 같으면 뜻을 유지하며 줄인다(조사 생략, 명사형, 약어).

## 쓸 수 있는 문자
- 한글 완성형 음절, ASCII(영문·숫자·공백·`!"#$%&'()*+,-./:;<=>?@[\]^_{|}~`)만.
- 쓰면 안 되는 문자: `·`, `…`, `“ ”`, `‘ ’`, `—`, `→`, `①` 등 특수 기호, 한자, 일본어. (따옴표는 ASCII `"` `'` 사용)

## 반드시 그대로 보존할 것
- 서식/치환 토큰: `%s %d %i %S2 %PN %UT %IL %IT %LO %SN ...` (퍼센트로 시작하는 모든 토큰), `{0}`, `\n`, 실제 줄바꿈, `\054` 같은 역슬래시 이스케이프
- 버튼/아이콘 토큰: `|L1| |R1| |L2| |R2| |CROSS| |CIRCLE| |SQUARE| |TRIANGLE| |START| |SELECT| |ANALOG| |RANALOG| |DPAD| |BULLET| |REG| |TM| |B| |/B| |U| |/U| |M_NEXTSUBPAGE|` 등 `|...|` 형태 전부 (안의 글자도 바꾸지 말 것)
- 대괄호/파이프로 된 링크 표시(예: `|Lineups|`)는 토큰이 아니라 화면에 보이는 링크 이름일 수 있음: 이메일의 `|Depth Chart|` 같은 것은 **파이프는 유지하고 안의 단어만 번역**(예: `|뎁스 차트|`). 단, 위의 버튼 토큰 목록에 있는 것은 절대 번역 금지.
- 문장 앞뒤 공백, 줄 끝 공백 개수는 대체로 원문과 맞춘다.

## 번역하지 않음 (null)
- 내부 식별자·키·파일명처럼 보이는 것: `FRONTENDOPTIONSCENES`, `Skybox3UnlockablesMenu`, `cam_HOF_go`, `Ump0`, `aA `, `TOU` 등
- 사람 이름(선수·코치·스태프), 곡 제목·아티스트, 브랜드·상표명(2K Sports, PlayStation, Topps 등) 단독 문자열
- 통계 약어 단독(AVG, HR, RBI, ERA, OPS, K, BB, W-L 등), 팀 약어(NYY, BOS 등), 포지션 약어(1B, SS, CF, P, DH 등)
- 의미를 알 수 없는 짧은 조각(문장 중간이 잘린 것 등)
- 애매하면 null 보다 번역 쪽을 택하되, 한 단어짜리 영문 대문자 키(예: `CATCHER`, `DARTS`)는 화면 표시용으로 보이면 번역해도 된다.

## 문체
- 메뉴·항목·버튼·제목: 명사형 간결체 (예: "Save Profile" → "프로필 저장", "Accept Trade" → "트레이드 수락")
- 설명·안내·도움말·매뉴얼: 합니다체 (예: "...할 수 있습니다.", "...하세요.")
- 확인 질문: "...하시겠습니까?"
- 이메일·GM 메시지·팀 미팅·선수 반응·스카우트 리포트: 등장인물의 말투를 살린 자연스러운 구어체 해요체/반말(원문 분위기에 맞춰), 감독(사용자)을 부를 때는 "감독님".
- 퀴즈: 질문은 "~은/는 무엇입니까?" 대신 자연스러운 "~은?" "~입니까?" 혼용 가능, 보기는 짧게.

## 고유명사
- 사람 이름은 영문 그대로 둔다(게임 로스터가 영문이므로). 예: "Randy Johnson은 ..." — 조사는 받침 여부를 발음 기준으로 맞춘다.
- 팀 이름·도시는 한글 음역: Yankees 양키스, Red Sox 레드삭스, Cubs 컵스, White Sox 화이트삭스, Mets 메츠, Dodgers 다저스, Giants 자이언츠, Cardinals 카디널스, Braves 브레이브스, Astros 애스트로스, Angels 에인절스, Athletics/A's 애슬레틱스, Mariners 매리너스, Rangers 레인저스, Twins 트윈스, Indians 인디언스, Tigers 타이거스, Royals 로열스, Orioles 오리올스, Blue Jays 블루제이스, Devil Rays 데블레이스, Marlins 말린스, Phillies 필리스, Nationals 내셔널스, Expos 엑스포스, Pirates 파이리츠, Reds 레즈, Brewers 브루어스, Rockies 로키스, Padres 파드리스, Diamondbacks/D-backs 다이아몬드백스
- 구장 이름: 음역(예: Wrigley Field 리글리 필드, Fenway Park 펜웨이 파크, Yankee Stadium 양키 스타디움)
- 리그: American League 아메리칸 리그(AL), National League 내셔널 리그(NL), World Series 월드시리즈, All-Star 올스타, Hall of Fame 명예의 전당, Cy Young 사이 영상, MVP 그대로, Rookie of the Year 신인왕, Gold Glove 골드 글러브, Silver Slugger 실버 슬러거

## 용어집
| 영어 | 한국어 |
|---|---|
| Play Ball / Quick Play | 플레이 볼 / 빠른 경기 |
| Exhibition | 시범 경기 |
| Franchise (mode) | 프랜차이즈 |
| Season | 시즌 |
| Playoffs / Postseason | 포스트시즌 (단독 메뉴는 "플레이오프" 허용) |
| Home Run Derby | 홈런 더비 |
| World Baseball Classic | 월드 베이스볼 클래식 |
| Manager Mode | 감독 모드 |
| Situation | 상황극 모드(메뉴) / 상황 |
| Tournament | 토너먼트 |
| Skybox | 스카이박스 |
| Trivia | 퀴즈 |
| VIP / VIP Profile | VIP / VIP 프로필 |
| Inside Edge | 인사이드 엣지 |
| Batter's Eye | 배터스 아이 |
| Payoff Pitch | 결정구 |
| Roster | 로스터 |
| Lineup | 라인업 |
| Depth Chart | 뎁스 차트 |
| Rotation | 선발 로테이션 |
| Bullpen | 불펜 |
| Starter / Reliever / Closer / Setup | 선발 / 구원 / 마무리 / 셋업 |
| Pitcher / Batter / Hitter / Catcher / Fielder / Runner | 투수 / 타자 / 타자 / 포수 / 야수 / 주자 |
| First Base / Second / Third / Shortstop | 1루(수) / 2루(수) / 3루(수) / 유격수 |
| Left / Center / Right Field | 좌익(수) / 중견(수) / 우익(수) |
| Designated Hitter | 지명타자 |
| Pinch Hitter / Pinch Runner | 대타 / 대주자 |
| Strikeout / Walk / Hit By Pitch | 삼진 / 볼넷 / 몸에 맞는 공 |
| Single / Double / Triple / Home Run | 단타 / 2루타 / 3루타 / 홈런 |
| Stolen Base / Caught Stealing | 도루 / 도루 실패 |
| RBI / Batting Average / ERA | 타점 / 타율 / 평균자책점 |
| Pickoff / Pitchout / Intentional Walk | 견제 / 피치아웃 / 고의사구 |
| Leadoff (주자 리드) | 리드 |
| Bunt / Sacrifice | 번트 / 희생 |
| Inning / Out / Strike / Ball / Count | 이닝 / 아웃 / 스트라이크 / 볼 / 카운트 |
| Fastball / Curveball / Slider / Changeup / Sinker / Splitter / Cutter / Knuckleball / Forkball / Screwball | 패스트볼 / 커브 / 슬라이더 / 체인지업 / 싱커 / 스플리터 / 커터 / 너클볼 / 포크볼 / 스크루볼 |
| 4-seam / 2-seam | 포심 / 투심 |
| Trade | 트레이드 |
| Free Agent | 자유계약선수(FA) |
| Draft | 드래프트 |
| Minor Leagues / Call-up / Send down | 마이너리그 / 콜업 / 마이너 강등 |
| Injury / Disabled List | 부상 / 부상자 명단 |
| Contract / Salary / Payroll | 계약 / 연봉 / 총연봉 |
| Owner / General Manager (GM) / Scout | 구단주 / 단장(GM) / 스카우트 |
| Spring Training | 스프링 캠프 |
| Ratings / Overall | 능력치 / 종합 |
| Contact / Power / Speed / Arm / Range / Fielding / Durability | 컨택트 / 파워 / 스피드 / 송구 / 수비 범위 / 수비 / 내구성 |
| Stamina / Control / Velocity / Break | 체력 / 제구 / 구속 / 변화 |
| Fatigue / Composure / Confidence / Temper | 피로 / 평정심 / 자신감 / 성질 |
| Difficulty (Rookie/Pro/All-Star/Legend) | 난이도 (루키/프로/올스타/레전드) |
| Profile / Save / Load / Delete | 프로필 / 저장 / 불러오기 / 삭제 |
| Memory Card (PS2) | 메모리 카드(PS2) |
| Options / Settings / Controls | 옵션 / 설정 / 조작 |
| Audio / Music / Soundtrack | 오디오 / 음악 / 사운드트랙 |
| Camera | 카메라 |
| Replay | 리플레이 |
| Cheats / Unlockables | 치트 / 잠금 해제 항목 |
| Trophy / Award | 트로피 / 상 |
| Online / Lobby / Friends / Rankings / Leaderboard | 온라인 / 로비 / 친구 / 랭킹 / 순위표 |
| Yes / No / OK / Cancel / Back / Continue / Done / Accept / Decline | 예 / 아니요 / 확인 / 취소 / 뒤로 / 계속 / 완료 / 수락 / 거절 |
| Home / Away | 홈 / 원정 |
| Standings / Schedule / League Leaders | 순위 / 일정 / 리그 리더 |
| Box Score | 박스 스코어 |
| Player Card | 선수 카드 |
| Edit Player / Create Player | 선수 편집 / 선수 생성 |
| Stadium / Ballpark | 구장 |
| Umpire | 심판 |
