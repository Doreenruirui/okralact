# -*- coding: utf-8 -*-
#
# Copyright 2015 Benjamin Kiessling
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing
# permissions and limitations under the License.

from collections import defaultdict
from typing import Callable, Any, BinaryIO, List, Tuple
#from contextlib import closing

import urllib
import requests
import json
import os


def publish_model(access_token:str, model_file:str, remote_file:str, ocr_engine:str, license_name:str, metadata: dict, related_DOI:List[Tuple[str,str]]=None, is_draft=False) -> str:
    md_upload_title       = 'FOO model for %s' % ocr_engine # this is the upload title on Zenodo
    md_upload_description = 'This file can be loaded by %s' % ocr_engine # this is the description text in Zenodo
    md_upload_keywords    = ['iddqd'] # ocr? ocr_engine? you know more than me what should be there
    md_upload_communities = [{'identifier': 'iddqd'}] # we should look at which Zenodo communities might fit here, and then uncomment the usage of this variable
    md_upload_creators    = [{'name': 'Automatic Method', 'affiliation': 'Python Script'}] # do you think there is a way to do better?
    
    relations = ('isCitedBy', 'cites', 'isSupplementTo', 'isSupplementedBy', 'isNewVersionOf', 'isPreviousVersionOf', 'isPartOf', 'hasPart', 'compiles', 'isCompiledBy', 'isIdenticalTo', 'isAlternateIdentifier')
    if not related_DOI is None:
        for r in related_DOI:
            if not r[0] in relations:
                raise Exception('relation (element 0) from related_DOI has value %s but must be in ' % r[0], relations)
    
    headers = {"Content-Type": "application/json"}
    # Asks for a deposition id
    r = requests.post('https://zenodo.org/api/deposit/depositions', params={'access_token': access_token}, json={}, headers=headers)
    deposition_id = r.json()['id']
    # Uploads the model
    data = {'name': remote_file}
    files = {'file': open(model_file, 'rb')}
    r = requests.post('https://zenodo.org/api/deposit/depositions/%s/files' % deposition_id, params={'access_token': access_token}, data=data, files=files)
    # Uploads the model metadata
    if not metadata is None:
        data = {'filename': 'metadata.json'}
        files = {'file': ('metadata.json', json.dumps(metadata))}
        r = requests.post('https://zenodo.org/api/deposit/depositions/%s/files' % deposition_id,
                params={'access_token': access_token}, data=data,
                files=files
        )
    # Uploads the submission metadata
    related = [{'relation': 'isCompiledBy', 'identifier': '10.1145/3352631.3352638'}]
    if not related_DOI is None:
        for r in related_DOI:
            related.append({'relation': r[0], 'identifier': r[1]})
    data = {
        'metadata': {
            'title': md_upload_title,
            'upload_type': 'dataset',
            'publication_type': 'other',
            'description': md_upload_description,
            'creators': md_upload_creators,
            'license': license_name,
            'related_identifiers': related,
            'communities': md_upload_communities,
            'keywords': md_upload_keywords,
            'access_right': 'open'
        }
    }
    r = requests.put('https://zenodo.org/api/deposit/depositions/%s' % deposition_id, params={'access_token': access_token}, data=json.dumps(data), headers=headers)
    
    # Confirm the upload and get a DOI
    # if not draft:
    r = requests.post('https://zenodo.org/api/deposit/depositions/%s/actions/publish' % deposition_id,
                      params={'access_token': access_token} )
    r.raise_for_status()
    return r.json()['doi']
    # else:
    # return 'unpublished, id=%s' % deposition_id
