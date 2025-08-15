import json
import os.path

import pandas as pd
from numpy.ma.extras import column_stack
QUESTION_CONSTANT = 1000
'''
Final version as on 03/03/2025.
Todo: support excel formate file, instead of CSV.
'''
def createOutData(out_folder, data, sheetname):
    if not os.path.exists(out_folder) :
        os.makedirs(out_folder)
    filename=f'{out_folder}/{sheetname}.json'
   # with open(filename,'w') as file:
   #     file.write(data)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
   
    print(f"OUTFIE :::::::::::::::: {filename}")

def main():
    FPATH = '.'
    FNAME = 'input/QAFromSonu_1Jul2025_ThaiLang_2.xlsx'  # Updated to Excel file
    FILE_NAME = f'{FPATH}/{FNAME}'
    SUBFOLDERS_PATH = './data_out'
    all_sheets = pd.read_excel(FILE_NAME, sheet_name=None)
    for sheet_name, df in all_sheets.items():
        print(f"Processing sheet: {sheet_name}")
        df.to_csv(f'{SUBFOLDERS_PATH}/{sheet_name}.csv', index=False, encoding='utf-8')
        # Replace 'your_file.xlsx' with the path to your Excel file
        #file_path = f'{FILE_NAME}'
        #df = pd.read_excel(file_path)  # Updated to read Excel file
        df = df.iloc[:, 1:]
        # df = df.iloc[:,2:]
        print(df.columns)
        df.fillna('No', inplace=True)
        df.replace('No', None, inplace=True)

        gQuestion = None
        lquestion = None

        total_questions=0
        answered_questions=0
        section_id = 0
        #questionsMap={}

        isFirst = True
        currentSectionsQuestionList=[]

        fullJsonList = []
        for index, row in df.iterrows():
            questionary_id = ((section_id + 1) * QUESTION_CONSTANT) + index
            currentQuestionsListMap = {}
            currentQuestionsList = []        #   Holds 3 questions as list
            question1Dict = {}       #   Question-1

        ##########################
            audio_notes = row['audio_notes']
            total_questions = total_questions + 1
            if audio_notes is None:
                total_questions = total_questions - 1
                #Create directory...
                #print(f"Skipping........... row {index}.")
                if isFirst == False:
                    currentSectionMap = {}
                    section_id = section_id + 1
                    currentSectionMap["category_id"] = section_id
                    currentSectionMap["titile"] = gQuestion
                    currentSectionMap['answered_questions'] = 0
                    currentSectionMap['total_questions'] = total_questions
                    currentSectionMap['questionary'] = currentSectionsQuestionList
                    fullJsonList.append(currentSectionMap)
                    total_questions = 0
                    currentSectionsQuestionList = []
                gQuestion = row['question']
                isFirst = False
                continue

            audioNotesDict = {}
            question1Dict["question_id"] = str(questionary_id)+""+str(1)
            question = row['question']
            question1Dict['question_description'] = question
            #audio_notes  = row['audio_notes']
            if audio_notes is None or str(audio_notes).strip().lower() == 'no':
                audioNotesDict['path'] = None
            else:
                audioNotesDict['path'] = audio_notes

            question1Dict['audio_note_url'] = audioNotesDict['path']
        ##########################
            photoThumbNailDict ={}
            photo_thumbnail =  row['photo_thumbnail']
            if photo_thumbnail is None or str(photo_thumbnail).strip().lower() == 'no':
                photoThumbNailDict['path'] =  None
            else:
                photoThumbNailDict['path'] = 'PathToFile'

            question1Dict['photo_note_url'] = photoThumbNailDict['path']
        ##########################
            videoThumbnailDict = {}
            video_thumbnail =  row['video_thumbnail']
            if video_thumbnail is None or str(video_thumbnail).strip().lower() == 'no':
                videoThumbnailDict['path'] =  None
            else:
                videoThumbnailDict['path'] = 'PathToFile'
            question1Dict['video_note_url'] = videoThumbnailDict['path']
        ##########################

            multiple_choice_options =  row['multiple_choice_options']
            if multiple_choice_options is None or str(multiple_choice_options).strip().lower() == 'no':
                question1Dict['select_options'] = None
            else:
                _multiple_choice_options_lst = multiple_choice_options.split(',')
                __multiple_choice_options_lst = [element.strip() for element in _multiple_choice_options_lst]
                multiple_choice_options_lst = []
                for l in __multiple_choice_options_lst:
                    lmcoMap = {}
                    lmcoMap['choice'] = l
                    lmcoMap['selected'] = False
                    multiple_choice_options_lst.append(lmcoMap)
                choiceOptionData = {}
                choiceOptionData['type']='single_select' #SingleSelect/MultiSelect/Text
                choiceOptionData['question_description'] = question
                choiceOptionData['choices'] = multiple_choice_options_lst
                question1Dict['select_options'] = choiceOptionData

    #--------------$ DONE TILL HERE ------

            ## upload section specific to question1:
            ##########################
            uploadsDict = {}
            uploadsMap = {}
            upload_photo = row['upload_photo']
            photosUploadDict = {}
            if upload_photo is None or str(upload_photo).strip().lower() == 'no':
                photosUploadDict['is_required'] = False
                photosUploadDict['is_mandatory'] = False
                photosUploadDict['path'] = None
            else:
                photosUploadDict['is_required'] = True
                photosUploadDict['is_mandatory'] = True
                photosUploadDict['path'] = None  # "NewPhotoPath"
            uploadsDict['photo'] = photosUploadDict
            uploadsMap['photo'] = uploadsDict['photo']
            ##########################
            videoUploadDict = {}
            upload_video = row['upload_video']
            if upload_video is None or str(upload_video).strip().lower() == 'no':
                videoUploadDict['is_required'] = False
                videoUploadDict['is_mandatory'] = False
                videoUploadDict['path'] = None
            else:
                videoUploadDict['is_required'] = True
                videoUploadDict['is_mandatory'] = True
                videoUploadDict['path'] = None  # "NewVideoPath"
            uploadsDict['video'] = videoUploadDict
            uploadsMap['video'] = uploadsDict['video']
            ##########################
            audioUploadDict = {}
            upload_audio = row['upload_audio']
            if upload_audio is None or str(upload_audio).strip().lower() == 'no':
                audioUploadDict['is_required'] = False
                audioUploadDict['path'] = None
            else:
                audioUploadDict['is_required'] = True
                audioUploadDict['is_mandatory'] = False
                audioUploadDict['path'] = None  # "NewAudioPath"
            uploadsDict['audio'] = audioUploadDict
            uploadsMap['audio'] = uploadsDict['audio']

            question1Dict['uploads'] = uploadsMap

            #currentQuestionsList.append(question1Dict)
    ##############################################  SUB QUESITON 1 #################################################
            question2Dict = {}

            is_sub1_question =  row['is_sub1_question']
            question2Dict["question_id"] = str(questionary_id)+""+str(2)
            if is_sub1_question is None or str(is_sub1_question).strip().lower() == 'no':
                question2Dict['is_required'] = False
            else:
                question2Dict['is_required'] = True

            ##########################
            sub1AudioNotesDict = {}
            sub1_audio_notes = row['sub1_audio_notes']

            if sub1_audio_notes is None or str(sub1_audio_notes).strip().lower() == 'no':
                #sub1AudioNotesDict['is_required'] = False
                sub1AudioNotesDict['path'] = None
            else:
                #sub1AudioNotesDict['is_required'] = True
                sub1AudioNotesDict['path'] = sub1_audio_notes

            #question2Dict['audio_notes'] = sub1AudioNotesDict
            question2Dict['audio_note_url'] = sub1AudioNotesDict['path']
            question2Dict['image_note_url'] = None
            question2Dict['video_note_url'] = None
            question2Dict['uploads'] = None
            ##########################

            sub1_question =  row['sub1_question']
            if sub1_question is None or str(sub1_question).strip().lower() == 'no':
                question2Dict['question_description'] = None
            else:
                question2Dict['question_description'] = sub1_question

            ##########################
            sub1_multiple_choice_options =  row['sub1_multiple_choice_options']
            if sub1_multiple_choice_options is None or str(sub1_multiple_choice_options).strip().lower() == 'no':
                question2Dict['select_options'] = None
            else:
                _sub1_multiple_choice_options = sub1_multiple_choice_options.split(',')
                __sub1_multiple_choice_options = [element.strip() for element in _sub1_multiple_choice_options]
                sub1_multiple_choice_options_lst = []
                for l in __sub1_multiple_choice_options:
                    lmcoMap = {}
                    lmcoMap['choice'] = l
                    lmcoMap['selected'] = False
                    sub1_multiple_choice_options_lst.append(lmcoMap)
                choice2OptionData = {}
                choice2OptionData['type'] = 'single_select'  # SingleSelect/MultiSelect/Text
                choice2OptionData['question_description'] = sub1_question
                choice2OptionData['choices'] = sub1_multiple_choice_options_lst
                question2Dict['select_options'] = choice2OptionData

            #questionaryList.append(subQuestion1Dict)
            if False == question2Dict['is_required']:
                question1Dict['sub_question'] = None
            else:
                question1Dict['sub_question'] = question2Dict
                #currentQuestionsList.append(question2Dict)
            #my_json_dict['sub_question_1'] = subQuestion1Dict
    ##############################################    SUB QUESITON 2 #######################################
            question3Dict = {}
            question3Dict["question_id"] = str(questionary_id)+""+str(3)
            is_sub2_question =  row['is_sub2_question']
            if is_sub2_question is None or str(is_sub2_question).strip().lower() == 'no':
                question3Dict['is_required'] = False
            else:
                question3Dict['is_required'] = True
            ##########################
                sub2AudioNotesDict = {}
                sub2_audio_notes = row['sub2_audio_notes']

                if sub2_audio_notes is None or str(sub2_audio_notes).strip().lower() == 'no':
                    #sub2AudioNotesDict['is_required'] = False
                    sub2AudioNotesDict['path'] = None
                else:
                    #sub2AudioNotesDict['is_required'] = True
                    sub2AudioNotesDict['path'] = sub2_audio_notes

                #question3Dict['audio_notes'] = sub2AudioNotesDict
                question3Dict['audio_note_url'] = sub2AudioNotesDict['path']
                question3Dict['image_note_url'] = None
                question3Dict['video_note_url'] = None
                question3Dict['uploads'] = None
            ##########################
            sub2_question =  row['sub2_question']
            if sub2_question is None or str(sub2_question).strip().lower() == 'no':
                question3Dict['question_description'] = None
            else:
                question3Dict['question_description'] = sub2_question
            ##########################

            sub2_multiple_choice_options =  row['sub2_multiple_choice_options']
            if sub2_multiple_choice_options is None or str(sub2_multiple_choice_options).strip().lower() == 'no':
                question3Dict['select_options'] = None
            else:
                _sub2_multiple_choice_options_lst = sub2_multiple_choice_options.split(',')
                __sub2_multiple_choice_options_lst = [element.strip() for element in _sub2_multiple_choice_options_lst]
                sub2_multiple_choice_options_lst = []
                for l in __sub2_multiple_choice_options_lst:
                    lmcoMap = {}
                    lmcoMap['choice'] = l
                    lmcoMap['selected'] = False
                    sub2_multiple_choice_options_lst.append(lmcoMap)
                    choice3OptionData = {}
                    choice3OptionData['type'] = 'single_select'  # SingleSelect/MultiSelect/Text
                    choice3OptionData['question_description'] = sub2_question
                    choice3OptionData['choices'] = sub2_multiple_choice_options_lst
                question3Dict['select_options'] = choice3OptionData
                question3Dict['sub_question'] = None
            #currentQuestionsList.append(question3Dict)  #All 3 questions are in list now.
            # questionaryList.append(subQuestion1Dict)
            if question3Dict['is_required'] == False:
                question2Dict['sub_question'] = None
            else:
                question2Dict['sub_question'] = question3Dict
            currentQuestionsList.append(question1Dict) #question1Dict -> question2Dict -> question3Dict #All 3 questions are in list now.

            currentQuestionsListMap["questionary_id"] = questionary_id
            currentQuestionsListMap["questions"] = currentQuestionsList[0]

            print(f"currentQuestionsListMap  : {currentQuestionsListMap}" )
            print(f"{sheet_name} : XXXXXXXXXX: {index}")
            currentSectionsQuestionList.append( currentQuestionsListMap )
            #print(json.dumps(my_json_dict))
            #createOutData(out_folder, json.dumps(my_json_dict), index)
        section_id = section_id + 1
        currentSectionMap = {}
        currentSectionMap["category_id"] = section_id
        currentSectionMap["titile"] = gQuestion
        currentSectionMap['answered_questions'] = 0
        currentSectionMap['total_questions'] = total_questions
        currentSectionMap['questionary'] = currentSectionsQuestionList
        fullJsonList.append(currentSectionMap)
        createOutData("data_out", fullJsonList, sheet_name)
        #return json.dumps(fullJsonList)

out = main()
#createOutData("data_out", out, "testttttttttt")
print("*"*30)
#print (out)
print("*"*30)
