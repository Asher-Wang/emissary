package detectlicense

import (
	"strings"
)

var (
	reMIT = reCompile(reCaseInsensitive(`\s*` +
		// Any number of license-name, copyright-holder, or header-separator lines
		`((` +
		strings.Join([]string{
			`\(?(The )?MIT License( \((MIT|Expat)\))?\)?`,
			`(Portions )?Copyright [^\n]*(\s+All rights reserved\.)?`, // copyright line
			`[^\n]{0,15}`,  // project name
			`https?://\S+`, // project url
			`=+`,           // separator
		}, `|`) +
		`)\s*\n\s*)*` +
		// The license itself
		reWrap(``+
			`Permission is hereby granted, free of charge, to any person obtaining`+"\n"+
			`a copy of this software and associated documentation files \(the`+"\n"+
			`["“']Software["”']\), to deal in the Software without restriction, including`+"\n"+
			`without limitation the rights to use, copy, modify, merge, publish,`+"\n"+
			`distribute, sublicense, and/or sell copies of the Software, and to`+"\n"+
			`permit persons to whom the Software is furnished to do so, subject to`+"\n"+
			`the following conditions:`+"\n"+
			``+
			`The above copyright notice and this permission notice shall be`+"\n"+
			`included in all copies or substantial portions of the Software\.`+"\n"+
			``+
			`THE SOFTWARE IS PROVIDED ["“']AS IS["”'], WITHOUT WARRANTY OF ANY KIND,`+"\n"+
			`EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF`+"\n"+
			`MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND`+"\n"+
			`NONINFRINGEMENT\. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE`+"\n"+
			`LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION`+"\n"+
			`OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION`+"\n"+
			`WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE\.?\s*`)))

	reMIT2 = reCompile(reCaseInsensitive(`\s*`+
		// Any number of license-name, copyright-holder, or header-separator lines
		`((`+
		strings.Join([]string{
			`\(?(The )?MIT License( \((MIT|Expat)\))?\)?`,
			`(Portions )?Copyright [^\n]*(\s+All rights reserved\.)?`, // copyright line
			`[^\n]{0,15}`,  // project name
			`https?://\S+`, // project url
			`=+`,           // separator
		}, `|`)+
		`)\s*\n\s*)*`+
		// The license itself
		reWrap(``+
			`Permission is hereby granted, free of charge, to any person obtaining a copy`+"\n"+
			`of this software and associated documentation files \(the ["“']Software["”']\), to deal`+"\n"+
			`in the Software without restriction, including without limitation the rights`+"\n"+
			`to use, copy, modify, merge, publish, distribute, sublicense, and/or sell`+"\n"+
			`copies of the Software, and to permit persons to whom the Software is`+"\n"+
			`furnished to do so, subject to the following conditions:`+"\n"+
			``+
			`The above copyright notice and this permission notice shall be included in`+"\n"+
			`all copies or substantial portions of the Software.`+"\n"+
			``+
			`THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR`+"\n"+
			`IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,`+"\n"+
			`FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE`+"\n"+
			`AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER`+"\n"+
			`LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,`+"\n"+
			`OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN`+"\n"+
			`THE SOFTWARE\.?\s*`)+
		`- Based on [^\n]*\n\s*`) +
		reWrap(`"""
The MIT License \(MIT\)

Copyright \(c\) 2013 Oguz Bilgic

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files \(the "Software"\), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""`) + `\s*`)
)
